HSP2, Hydrologic Simulation Program Python (HSPsquared)
=======================================================
HSPsquared or HSP2 is a Python version of HSPF. Currently it supports the major
hydrology modules.  It is copyrighted by RESPEC and released under the GNU
Affero General Public License.


MAJOR REPOSITORY DIRECTORIES
============================
**HSP2** contains the hydrology codes converted from HSPF and the main programs
to run HSP2. This software is Python with dependency on Pandas and Numba (open
source) libraries.

**HSP2notebooks** contains tutorials and useful Juptyer Notebooks.  Some of the
tutorials demonstrate capabilities that require additional Python modules (like
Networkx and matplotlib.)

**HSP2tools** contains supporting software modules such as the code to convert
legacy WDM and UCI files to HDF5 files for HSP2, and to provide additional new
and legacy capabilities.

Early version of this library used Tim Cera's open source code for HSPF
(i.e. wdmtoolbox_, tstoolbox_, and hspfbintoolbox_; see commit c259f32_), but they 
have since been deleted from this repo, likely after the HSP2 versions were proven to work.

.. _wdmtoolbox: https://github.com/timcera/wdmtoolbox
.. _tstoolbox: https://github.com/timcera/tstoolbox
.. _hspfbintoolbox: https://github.com/timcera/hspfbintoolbox
.. _c259f32: https://github.com/respec/HSPsquared/tree/c259f32cc927402ce8506e4243c9b54091b9a446

INSTALLATION INSTRUCTIONS
=========================

The installation instructions have been revised to utilize an environment.yml file to help with setting up you python 2.7 environment. Please reference the [Set up & Installation](https://github.com/LimnoTech/HSPsquared/wiki/Set-up-&-Installation) wiki page for installation instructions. 

TUTORIALS and JUPYTER NOTEBOOKS
===============================
You should be able to start the Tutorials and other Jupyter Notebooks once you
have finished the installation steps above.  In Enthought's Canopy distribution
you can simply click on the desired file - but this is amazingly slow since it
starts Canopy which in turn eventually starts the Notebook.  The easiest way
with either Anaconda or Enthought is to open a command window, move (CD) to the
location where you put the HSP2 unzipped file, and then type "jupyter notebook"
at the command prompt.  You will see the Jupyter Notebook open a file browser
window. Click on the desired Tutorial.  If you are using the Enthought Python
distribution, Canopy, look for "Enthought Canopy" under the Windows "All
Programs" to find the "Enthought Canopy Command Window" to use.  You can pin
this to either your task bar or start window to make starting Notebooks easy.

There is also a YouTube video available at https://youtu.be/aeLScKsP1Wk to get
you inroduced to HSP2.

NOTE: As a Jupyter project security step, the first time you start any Jupyter
Notebook, you may need to look at this message in the command window:
"Copy/past this  URL into your browser when you connect for the first time, to
login with a token:".  You should copy and paste the following line into your
browser.  You will NOT need to do this again.  The Jupyter system wants to
insure that you are authorizing the Jupyter server to run on your system.  This
is in rapid change to a password based authorization, so follow the
instructions in the command window.
