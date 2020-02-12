#!/usr/bin/env seiscomp-python
#
# Dump moment tensor information to text.
#
# Could be invoked in a pipeline like:
#
#  python scxmldump-public-with-mt.py --debug -d "$db" -E "$evid" |
#  python scxml-to-mt-bulletin.py
#

import sys
from math import sin, cos, log10, sqrt, atan2, pi
import seiscomp.client, seiscomp.datamodel, seiscomp.io
import seiscomp.seismology

def radiationPattern(Mxx, Myy, Mzz, Mxy, Mxz, Myz, azi, inc):
    # Parameters:
    #   Moment tensor elements
    #   azimuth, incidence angle in degrees
    #
    # Returns:
    #   P, SV, SH radiation patterns

    # For the angles see Pujol (9.9.16) etc.  phi==azi theta==inc

    cosazi = cos(azi*pi/180)
    sinazi = sin(azi*pi/180)
    cosinc = cos(inc*pi/180)
    sininc = sin(inc*pi/180)

    # Gamma, Theta, Phi are unit vectors:
    #
    # Gamma points away from the source (P direction)
    # Theta points in the direction of increasing incidence angle (SV plane)
    # Phi points in the direction of increasing azimuth (SH plane)
    #
    # See Pujol fig. 9.10

    Gamma_x  =  sininc*cosazi
    Gamma_y  =  sininc*sinazi
    Gamma_z  =  cosinc

    Theta_x  =  cosinc*cosazi
    Theta_y  =  cosinc*sinazi
    Theta_z  = -sininc

    Phi_x  = -sinazi
    Phi_y  =  cosazi
    Phi_z  =  0

    M_Gamma_x = Mxx*Gamma_x + Mxy*Gamma_y + Mxz*Gamma_z
    M_Gamma_y = Mxy*Gamma_x + Myy*Gamma_y + Myz*Gamma_z
    M_Gamma_z = Mxz*Gamma_x + Myz*Gamma_y + Mzz*Gamma_z

    P  = Gamma_x*M_Gamma_x + Gamma_y*M_Gamma_y + Gamma_z*M_Gamma_z
    SV = Theta_x*M_Gamma_x + Theta_y*M_Gamma_y + Theta_z*M_Gamma_z
    SH =   Phi_x*M_Gamma_x +   Phi_y*M_Gamma_y +   Phi_z*M_Gamma_z

    return P, SV, SH


def renderTensor(Mxx, Myy, Mzz, Mxy, Mxz, Myz, nx=33, ny=19):
    """
    Renders the tensor as textual beachball graphics with nx columns
    and ny rows.

    Returns a text string.

    The default dimension 33x19 is like in the GEOFON MT bulletin emails.
    """
    txt = ""
    for iy in range(ny):
        y = 2.*((ny-iy-0.5)-ny/2)/ny
        line = ""
        for ix in range(nx):
            x = 2.*((ix+0.5)-nx/2)/nx
            r = sqrt(x**2+y**2)
            if r>1:
                line += " "
                continue
            azi = atan2(x,y)*180/pi
            inc = r*90
            rp,rsv,rsh = radiationPattern(Mxx, Myy, Mzz, Mxy, Mxz, Myz, azi, inc)
            if rp > 0:
                line += "#"
            else:
                line += "-"
        txt += "%s\n" % line
    return txt


def SC32Bulletin(fm):
    """
    Generate "bulletin" style output for a given focal mechanism
    """

    try:
        np_str =  fm.nodalPlanes().nodalPlane1().strike()
        np_dip =  fm.nodalPlanes().nodalPlane1().dip()
        np_rake = fm.nodalPlanes().nodalPlane1().rake()
    except:
        seiscomp.logging.error("Cannot determine nodal planes")
        return

    if fm.momentTensorCount() == 0:
        seiscomp.logging.error("FocalMechanism without MomentTensor")
        return 

    mt = fm.momentTensor(0)
    mag = seiscomp.datamodel.Magnitude.Find(mt.momentMagnitudeID())
    if not mag:
        seiscomp.logging.error("Magnitude %s not found", mt.momentMagnitudeID())
        return

    triggeringOrigin = seiscomp.datamodel.Origin.Find(fm.triggeringOriginID())
    if not triggeringOrigin:
        seiscomp.logging.error("Triggering origin %s not found", fm.triggeringOriginID())
        return

    derivedOrigin = seiscomp.datamodel.Origin.Find(mt.derivedOriginID())
    if not derivedOrigin:
        seiscomp.logging.error("Derived origin %s not found", mt.derivedOriginID())
        return

    isCentroid = False
    try:
        if derivedOrigin.type() == seiscomp.datamodel.CENTROID:
            isCentroid = True
    except:
        pass

    tim = triggeringOrigin.time().value().toString("%y/%m/%d %H:%M:%S.%1f")
    lat = triggeringOrigin.latitude().value()
    lon = triggeringOrigin.longitude().value()
    regionName = seiscomp.seismology.Regions.getRegionName(lat, lon)
    mw = mag.magnitude().value()
    try:
        agencyID = m.creationInfo().agencyID()
    except:
        agencyID = "GFZ" # FIXME

    lines = []
    lines.append(tim)
    lines.append(regionName)
    lines.append("Epicenter: %.2f %.2f" % (lat, lon))
    lines.append("MW %.1f" % (mw))
    lines.append("")

    if isCentroid:
        lines.append("%s CENTROID MOMENT TENSOR SOLUTION" % agencyID)
        tim = derivedOrigin.time().value().toString("%y/%m/%d %H:%M:%S.%2f")
        lat = derivedOrigin.latitude().value()
        lon = derivedOrigin.longitude().value()
        lines.append("Centroid:  %.2f %.2f" % (lat, lon))
        lines.append(tim)
    else:
        lines.append("%s MOMENT TENSOR SOLUTION" % agencyID)

    depth = int(derivedOrigin.depth().value()+0.5)
    stationCount = derivedOrigin.quality().usedStationCount()
    lines.append("Depth: %3d %21s" % (depth, ("No. of sta: %d" % stationCount)))

    try:
        expo = 0
        tensor = mt.tensor()
        Mrr = tensor.Mrr().value()
        Mtt = tensor.Mtt().value()
        Mpp = tensor.Mpp().value()
        Mrt = tensor.Mrt().value()
        Mrp = tensor.Mrp().value()
        Mtp = tensor.Mtp().value()
        expo = max(expo, log10(abs(Mrr)))
        expo = max(expo, log10(abs(Mtt)))
        expo = max(expo, log10(abs(Mpp)))
        expo = max(expo, log10(abs(Mrt)))
        expo = max(expo, log10(abs(Mrp)))
        expo = max(expo, log10(abs(Mtp)))

        Tval = fm.principalAxes().tAxis().length().value()
        Nval = fm.principalAxes().nAxis().length().value()
        Pval = fm.principalAxes().pAxis().length().value()

        expo = max(expo, log10(abs(Tval)))
        expo = max(expo, log10(abs(Nval)))
        expo = max(expo, log10(abs(Pval)))
        expo = int(expo)

        Tdip = fm.principalAxes().tAxis().plunge().value()
        Tstr = fm.principalAxes().tAxis().azimuth().value()
        Ndip = fm.principalAxes().nAxis().plunge().value()
        Nstr = fm.principalAxes().nAxis().azimuth().value()
        Pdip = fm.principalAxes().pAxis().plunge().value()
        Pstr = fm.principalAxes().pAxis().azimuth().value()

        lines.append("Moment Tensor;   Scale 10**%d Nm" % expo)
        q = 10**expo
        lines.append("  Mrr=%5.2f       Mtt=%5.2f" % (Mrr/q, Mtt/q))
        lines.append("  Mpp=%5.2f       Mrt=%5.2f" % (Mpp/q, Mrt/q))
        lines.append("  Mrp=%5.2f       Mtp=%5.2f" % (Mrp/q, Mtp/q))

        lines.append("Principal axes:")
        lines.append("  T  Val= %5.2f  Plg=%2d  Azm=%3d" % (Tval/q, Tdip, Tstr))
        lines.append("  N       %5.2f      %2d      %3d" % (Nval/q, Ndip, Nstr))
        lines.append("  P       %5.2f      %2d      %3d" % (Pval/q, Pdip, Pstr))

        Mxx, Myy, Mzz, Mxy, Mxz, Myz = Mtt, Mpp, Mrr, -Mtp, Mrt, -Mrp
        txt = renderTensor(Mxx, Myy, Mzz, Mxy, Mxz, Myz)
        lines.append(txt)
    except:
        pass

    txt = "\n".join(lines)
    return txt


class MomentTensorDumper(seiscomp.client.Application):

    def __init__(self):
        argv = sys.argv
        seiscomp.client.Application.__init__(self, len(argv), argv)
        self.setMessagingEnabled(False)
        self.setDatabaseEnabled(False, False)
        self._xmlFile = "stdin"

    def _readEventParametersFromXML(self):
        ar = seiscomp.io.XMLArchive()
        if self._xmlFile == "stdin":
            fname = "-"
        else:
            fname = self._xmlFile
        if ar.open(fname) == False:
            raise IOError(self._xmlFile + ": unable to open")
        obj = ar.readObject()
        if obj is None:
            raise TypeError(self._xmlFile + ": invalid format")
        ep  = seiscomp.datamodel.EventParameters.Cast(obj)
        if ep is None:
            raise TypeError(self._xmlFile + ": no eventparameters found")
        return ep

    def run(self):
        ep = self._readEventParametersFromXML()

        for i in range(ep.focalMechanismCount()):
            fm = ep.focalMechanism(i)
            txt = SC32Bulletin(fm)
            print(txt)

        del ep
        return True


def main():
    app = MomentTensorDumper()
    app()

if __name__ == "__main__":
    main()
