#/bin/bash
SCRIPT=$(readlink -f $0)
SCRIPTDIR=$(dirname ${SCRIPT})
WORKDIR=${SCRIPTDIR}/tmp

# create working area
mkdir -p ${WORKDIR}

# clean up
rm -f ${WORKDIR}/Filmliste-akt.xz ${WORKDIR}/Filmliste-akt

# download and upack
wget -P ${WORKDIR} -q http://verteiler2.mediathekview.de/Filmliste-akt.xz
xz -d ${WORKDIR}/Filmliste-akt.xz

# process
python ${SCRIPTDIR}/updatefl.py ${WORKDIR}/Filmliste-akt

# clean up
rm -f ${WORKDIR}/Filmliste-akt.xz ${WORKDIR}/Filmliste-akt
