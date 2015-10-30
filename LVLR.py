#!/usr/bin/env pythonw
#!/usr/bin/env ffmpeg


#################################

# NPR Leveler
# NPR Labs, Copyright 2015
# Provides a platform-agnostic user interface for analyzing and 
# adjusting audio files to enforce compliance with EBU Loudness 
# standards.
# 
# This version is for DEBUGGING PURPOSES ONLY and has limited
# functionality.
#
# Project Leaders: Chris Nelson and Alice Goldfarb
# Principle Developers: Olivia Waring and Alice Goldfarb
# Installation assistance by Ty Von Plinsky
# Logo Artwork by Alice Goldfarb

#################################


# Dependencies:

import wx
import time
import os
import sys
import re
import subprocess
import shutil
from random import randint
from os.path import expanduser
from wx.lib.mixins.listctrl import CheckListCtrlMixin, ListCtrlAutoWidthMixin
from wx.lib.agw import ultimatelistctrl as ULC
import wx.lib.agw
import wx.html
import collections
import logging
from wx.lib.delayedresult import startWorker

app = wx.App(False)

work_dir = "/Applications"

log_name = work_dir + "/LVLR.app/Contents/my_log_file.txt"
log = open(log_name, 'w')
sys.stdout = log
sys.stderr = log

print "work_dir :=\n\t" + work_dir

command = work_dir + "/LVLR.app/Contents/MacOS/bin/ffmpeg"
print command

com = "echo $PATH"

print com

output_name = work_dir + "/LVLR.app/Contents/output_file_resultAnalyzeProducer.txt" ##
output_file = open(output_name, 'w') ##
print output_file
        #a = subprocess.Popen(['PATH=$PATH'], bufsize=1, stdout=output_file, stderr=output_file)
##        proc  = subprocess.Popen(['echo', '$PATH'], bufsize=1, stdout=output_file, stderr=output_file)
        #a = subprocess.call(['$PATH'], bufsize=1, stdout=output_file, stderr=output_file)
for d in sys.path:
    print d
print "\n"
sys.stdout.flush()
# Default settings:

TARGET_IL_DEFAULT = -24
TARGET_PEAK_DEFAULT = -2 
GRACE_DEFAULT = 2        # How far from the targetIL counts as 'within spec.'
ADJ_FILE_LOC_DEFAULT = os.getcwd()
LOG_FILE_LOC_DEFAULT = expanduser("~")
OVERWRITE_DEFAULT = True
SAME_FOLDER_DEFAULT = True
ADVANCED_ACCESS_DEFAULT = False

# OS-specific settings:

ffmpegEXE = command     # Windows: os.getcwd() + "\\FFMPEG\\bin\\ffmpeg.exe"   

SEPARATOR = '/'          # Windows: '\\' 

# Dictionary entry indices:

FILE_NAME = 0
MEETS_SPECS = 1 
INT_LOUD = 2
T_PEAK = 3
S_PEAK = 4
LOUDNESS_RANGE = 5
BITRATE = 6 
IS_RENDERED = 7
IS_ANALYZED = 8
IS_ADJUSTED = 9 
IS_MP = 10
MEETS_SPECS_ADJ = 11 
INT_LOUD_ADJ = 12
T_PEAK_ADJ = 13
S_PEAK_ADJ = 14
LOUDNESS_RANGE_ADJ = 15
IS_BAD = 16
IS_MONO = 17

# Miscellaneous Files:

#CONFIG_FILE = 'LevelerConfig.txt'

LOGO_IMG = work_dir + '/LVLR.app/Contents/level.png'
NPR_IMG = work_dir + '/LVLR.app/Contents/npr.png'

#subprocess.call([ffmpegEXE])
print command

class MainWindow(wx.Frame):
    """Build the primary Leveler window."""

    # Initialize session-specific data structures. 
 
    fileList = collections.OrderedDict()    # Primary file-storage data structure.
    buffer_list = []    # Stores recently deleted files.
    indexMap = []    # Maps the indices of the GUI list to the entries in fileList.

    # Specify allowed filetypes. 
    wildcard = "MP3 files (*.mp3)|*.mp3|WAV files (*.wav)|*.wav|M4A files (*.m4a)|*.m4a|AIFF files (*.aiff)|*.aiff|MP3 files (*.mp2)|*.mp2"
    allowedExtensions = ["MP3","mp3","WAV","wav","M4A","m4a","AIFF","aiff","MP2","mp2"]
    # ALICE: I use both of these data structures to keep track of allowed file extensions, but it would be lovely if we could link them somehow.

    def __init__(self, parent, id, title):
        """Initialize and display the main GUI window."""

        wx.Frame.__init__(self, parent, id, title, size=(1000, 500))

        # Initialize settings from the configuration file and log file. 
        
        self.config = {}
        #self.ReadConfig()

        self.currentIndex = 1
        
        if self.currentIndex == 1:
            self.targetPeak = TARGET_PEAK_DEFAULT 
            self.targetIL = TARGET_IL_DEFAULT 
            self.grace = GRACE_DEFAULT
            self.logFileLoc = LOG_FILE_LOC_DEFAULT
            self.adjFileLoc = ADJ_FILE_LOC_DEFAULT
            self.overwrite = OVERWRITE_DEFAULT
            self.advancedAccess = ADVANCED_ACCESS_DEFAULT
            self.sameFold = SAME_FOLDER_DEFAULT

#        else:
 
        # Construct horizontal menu bar.
        menubar = wx.MenuBar()
        about = wx.Menu()
        preferences = wx.Menu()
        help = wx.Menu()
 
        levelerInfoItem = about.Append(wx.NewId(), '&Leveler', 'Information about the Leveler')
        self.Bind(wx.EVT_MENU, self.OnLevelerInfo, levelerInfoItem)  

        loudnessInfoItem = about.Append(wx.NewId(), '&Loudness Standards', 'Overview of loudness standards')
        self.Bind(wx.EVT_MENU, self.OnLoudnessInfo, loudnessInfoItem)  

        labsInfoItem = about.Append(wx.NewId(), '&NPR Labs', 'Information about NPR Labs')
        self.Bind(wx.EVT_MENU, self.OnLabsInfo, labsInfoItem)  

        preferenceItem = preferences.Append(wx.NewId(), "Preferences", "Adjust Leveler settings")
        self.Bind(wx.EVT_MENU, self.OnPreferences, preferenceItem)  

        helpDocItem = help.Append(wx.NewId(), "&Documentation", "Guide to Leveler usage")
        self.Bind(wx.EVT_MENU, self.OnHelpDoc, helpDocItem)

        #helpVidItem = help.Append(wx.NewId(), "&Tutorial Video", "Video walktrhough of Leveler usage")
        #self.Bind(wx.EVT_MENU, self.OnHelpVid, helpVidItem)

        help.AppendSeparator()

        menubar.Append(about, '&About')
        menubar.Append(preferences, '&Settings')
        menubar.Append(help, '&LevelerHelp')
        self.SetMenuBar(menubar)

        # Add internal structure to the main frame.
        panel = wx.Panel(self, -1)
        vbox1 = wx.BoxSizer(wx.VERTICAL)
        vbox2 = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        buttonPanel = wx.Panel(panel, -1)
        filePanel = wx.Panel(panel, -1)

        # Construct the GUI's underlying file list.
        # ALICE: I used a module called "UltimateListCtrl" to build the GUI, becuase the normal list control
        #    does not support embedding progress bars into rows. If you need to make any further modifications, 
        #    refer to http://wxpython.org/Phoenix/docs/html/lib.agw.ultimatelistctrl.UltimateListCtrl.html 
        #    (there's also some semi-helpful information in the wxPython demo files).
        self.list = ULC.UltimateListCtrl(filePanel, agwStyle = wx.LC_REPORT | wx.LC_VRULES )
        self.list.InsertColumn(0, ' ', width=20)
        self.list.InsertColumn(1, 'Filename', wx.LIST_FORMAT_LEFT, width=300)
        self.list.InsertColumn(2, 'Progress', wx.LIST_FORMAT_CENTER, width=100)
        self.list.InsertColumn(3, 'Meets Specs?', wx.LIST_FORMAT_CENTER, width=100)
        self.list.InsertColumn(4, 'Integrated Loudness', wx.LIST_FORMAT_CENTER, width=130)
        self.list.InsertColumn(5, 'True Peak', wx.LIST_FORMAT_CENTER, width=100)
        self.list.InsertColumn(6, 'Peak Value', wx.LIST_FORMAT_CENTER, width=100)
        #self.list.InsertColumn(7, 'Loudness Range', wx.LIST_FORMAT_CENTER, width=100)

        # Establish file list as a drag-and-drop target.
        dropTarget = FileDrop(self.list, self)
        self.list.SetDropTarget(dropTarget)

        # Populate the button panel.
        self.loadfile = wx.Button(buttonPanel, -1, 'Upload File', size=(100, -1))
        self.loadfolder = wx.Button(buttonPanel, -1, 'Upload Folder', size=(100, -1))
        self.sel = wx.Button(buttonPanel, -1, 'Select All', size=(100, -1))
        self.sel.Disable()
        self.des = wx.Button(buttonPanel, -1, 'Deselect All', size=(100, -1))
        self.des.Disable()
        self.ana = wx.Button(buttonPanel, -1, 'Analyze', size=(100, -1))
        self.ana.Disable()
        self.adj = wx.Button(buttonPanel, -1, 'Adjust', size=(100, -1))
        self.adj.Disable()
        self.rem = wx.Button(buttonPanel, -1, 'Remove', size=(100,-1))
        self.rem.Disable()
        self.und = wx.Button(buttonPanel, -1, 'Undo Remove', size=(100, -1))
        self.und.Disable()

        # Add Leveler logo.
        img = wx.Image(LOGO_IMG, wx.BITMAP_TYPE_ANY)
        w = img.GetWidth()
        h = img.GetHeight()
        img_scaled = img.Scale(w/1, h/1) ##
        self.logo = wx.StaticBitmap(buttonPanel, -1, wx.BitmapFromImage(img_scaled))

        # Bind buttons to their respective functions.
        self.Bind(wx.EVT_BUTTON, self.OnLoadFile, id=self.loadfile.GetId())
        print "ID:: " + str(id)
        self.Bind(wx.EVT_BUTTON, self.OnLoadFolder, id=self.loadfolder.GetId())
        self.Bind(wx.EVT_BUTTON, self.OnRemove, id=self.rem.GetId())
        self.Bind(wx.EVT_BUTTON, self.OnUndo, id=self.und.GetId())
        self.Bind(wx.EVT_BUTTON, self.OnSelectAll, id=self.sel.GetId())
        self.Bind(wx.EVT_BUTTON, self.OnDeselectAll, id=self.des.GetId())
        self.Bind(wx.EVT_BUTTON, self.OnAnalyze, id=self.ana.GetId())
        self.Bind(wx.EVT_BUTTON, self.OnAdjust, id=self.adj.GetId())

        # Add NPR logo and copyright message.
        wmark = wx.Image(NPR_IMG, wx.BITMAP_TYPE_ANY)
        w = wmark.GetWidth()
        h = wmark.GetHeight()
        wmark_scaled = wmark.Scale(w/1, h/1) ##
        self.watermark = wx.StaticBitmap(filePanel, -1, wx.BitmapFromImage(wmark_scaled))
        self.copyright = wx.StaticText(filePanel, -1, "Copyright 2015 NPR Labs")

        # Set sizers.
        vbox1.Add(self.list, 1, wx.EXPAND | wx.TOP, 3)
        vbox1.Add((-1, 10))
        vbox1.Add(self.watermark,0, wx.ALIGN_BOTTOM | wx.ALIGN_CENTRE | wx.SHAPED)       
        vbox1.Add(self.copyright, 0, wx.ALIGN_BOTTOM | wx.ALIGN_CENTRE)
        filePanel.SetSizer(vbox1)

        vbox2.Add(self.logo, 0, wx.ALL, 10)
        vbox2.Add(self.loadfile, 0, wx.ALL, 10)
        vbox2.Add(self.loadfolder, 0, wx.ALL, 10)
        vbox2.Add(self.sel, 0, wx.ALL, 10)
        vbox2.Add(self.des, 0, wx.ALL, 10)
        vbox2.Add(self.rem, 0, wx.ALL, 10)
        vbox2.Add(self.und, 0, wx.ALL, 10)    # Disabled until applicable
        vbox2.Add(self.ana, 0, wx.ALL, 10)
        vbox2.Add(self.adj, 0, wx.ALL, 10)
        buttonPanel.SetSizer(vbox2)
  
        hbox.Add(buttonPanel, 0, wx.EXPAND | wx.RIGHT, 5)
        hbox.Add(filePanel, 1, wx.EXPAND)
        hbox.Add((3, -1))
        panel.SetSizer(hbox)

        # Initialize log file.
        logfilepath = self.logFileLoc + SEPARATOR + "NPRLevelerLogfile.txt" 
        if os.path.exists(logfilepath):
            self.logfile = open(logfilepath, 'a+')
        else:
            try: 
                self.logfile = open(logfilepath, 'w+')
            except:
                pass

        # Center and display main frame.
        self.Centre()
        self.Show(True)

    def OnQuit(self, event):
        self.Close()
           
    def OnPreferences(self, event):
        """Launch a settings dialog box."""

        dlg = SettingsDialog(self)
        dlg.ShowModal()
        dlg.Destroy()

    def OnLevelerInfo(self, event):
        """Launch a window that provides Leveler information."""

        description = """The NPR Leveler is a lightweight software application - currently available for PC and OSX - that automatically analyzes and adjusts audio files to ensure compliance with EBU loudness standards."""

        licence = """The NPR Leveler is free software, made available to all NPR member stations in the US to ensure consistent loudness levels across the American public radio landscape."""
        # ALICE: Do we need to reference the GNU General Public License? Or the Free Software Foundation? 
        #   I suppose legal can help clarify the requirements here...     

        info = wx.AboutDialogInfo()
        info.SetName('Leveler')
        info.SetVersion('1.0')
        info.SetDescription(description)
        info.SetCopyright('(C) 2015 NPR Labs')
        info.SetLicence(licence)
        info.AddDeveloper('Olivia Waring, Alice Goldfarb, Ty Von Plinsky, Chris Nelson')

        wx.AboutBox(info)

    def OnLoudnessInfo(self, event):
        """Launch a window that provides general information about loudness standards."""

        dlg = LoudnessInfoDialog(self)
        dlg.ShowModal()
        dlg.Destroy()

    def OnLabsInfo(self, event):
        """Launch a window that provides general information about NPR Labs."""

        dlg = LabsInfoDialog(self)
        dlg.ShowModal()
        dlg.Destroy()

    def OnHelpDoc(self, event):
        """To be implemented (hi ALICE!)"""
        pass

    #def OnHelpVid(self, event):  
        #pass



    def OnBadInput(self, file):
        """Notify the user of any invalid inputs."""

        self.fileList[file][IS_ANALYZED] = True
        self.fileList[file][IS_ADJUSTED] = True
        self.fileList[file][IS_BAD] = True
        message = wx.StaticText(self.panel, id=-1,style=wx.ALIGN_CENTRE, label="ffmpeg detected bad input for %s; check the extension on your file and ensure that your data has not been corrupted." % file)
        dlg = wx.MessageDialog(self, "Bad Input", message, style=wx.OK|wx.ICON_EXCLAMATION)
        dlg.ShowModal()

    def OnAnalyze(self, event):
        """The event handler for the 'Analyze' button."""

        # Calls the AnalyzeHelper method with the argument 'False' to indicate that
        # the 'Adjust' button has not also been triggered.
        print "OnAnalyze"

        self.AnalyzeHelper(False)

    def AnalyzeHelper(self, toAdjustLater):
        """Call an analysis thread for every selected item."""
        print "AnalyzeHelper\n\t toAdjustLater:" + str(self) + str(toAdjustLater)
        # Populate a list of selected files to be analyzed (ignoring any that have already been analyzed).
        toAnalyze = [] 

        for i in range(self.list.GetItemCount()):
            print "i (" + str(i) + ") of " + str(self.list.GetItemCount())
            if i%3 == 0:    # ALICE: Change this value to i%2 if you decide to get rid of the spacer 
                           # line (and do likewise where appropriate throughout the file).
              check = self.list.GetItem(i,0)
              box = check.GetWindow()
              file = self.indexMap[i/3]
              if box.GetValue() and not self.fileList[file][IS_ANALYZED]:
                toAnalyze.append((file,i))

        

        # Launch an analysis thread and progress bar for each selected file.
        for (file,index) in toAnalyze:
            item = self.list.GetItem(index,2)
            gauge = item.GetWindow()
            gauge.Pulse()
            ##self._resultAnalyzeProducer(file)  # Inserted for debugging purposes!
            self._resultAnalyzeProducer(file, index) 
          # analysisThread = startWorker(self._resultAnalyzeConsumer, self._resultAnalyzeProducer, cargs=(file,index,), wargs=(file,))
          # analysisThread.join()    # Stall processing until all analysis threads finish.
           
        # If the call to 'AnalyzeHelper' was initiated by pressing the 'Adjust' button, 
        # proceed to the AdjustHelper function. 
        if toAdjustLater:
			self.AdjustHelper()

    def OnAdjust(self, event):
        """The event handler for the 'Adjust' button."""
        print "OnAdjust\n"
        # Initiate analysis, while flagging files for post-analysis adjustment. 
        self.AnalyzeHelper(True)
                
    def AdjustHelper(self):
        """Call an adjust thread for every selected item."""
        # Compile list of selected files (ignoring any that have already been adjusted).
        toAdjust = []

        for i in range(self.list.GetItemCount()):
           if i%3 == 0:
               check = self.list.GetItem(i,0)
               box = check.GetWindow()
               file = self.indexMap[i/3]
               if box.GetValue() and not self.fileList[file][IS_ADJUSTED]:
                   toAdjust.append((file,i+1))

        # Perform adjustment for each selected item. 
        for (file,index) in toAdjust:
            

            # Add progress bars.
            item = self.list.GetItem(index,2)
            item._mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT | ULC.ULC_MASK_FONTCOLOUR
            width = self.list.GetColumnWidth(1)
            gauge = wx.Gauge(self.list,-1,range=50,size=(width,15),style=wx.GA_HORIZONTAL | wx.GA_SMOOTH)
            gauge.Pulse() #shouldn't start this right away...
            item.SetWindow(gauge, wx.ALIGN_CENTRE)
            self.list.SetItem(item) 

            # Display the names of the to-be-adjusted files.
            (dir,just_file) = os.path.split(os.path.abspath(file))
            dot = re.search("\.", just_file)
            extension = just_file[dot.end():]
            stem = just_file[:dot.end()-1]
            timestamp = time.strftime("%d-%m-%Y;%H%M") + '.'
            if not self.overwrite:
                adjusted_file = stem + "_adjusted_" + timestamp + extension
            else: 
                adjusted_file = stem + "_adjusted." + extension
            self.list.SetStringItem(index, 1, adjusted_file) 

            # Launch an adjust thread for each selected file.
            print "file name"
            print file
            print "TARGET:"
            print self.targetIL
            self._resultAdjustProducer(file, timestamp, index)
            # startWorker(self._resultAdjustConsumer, self._resultAdjustProducer, cargs=(file,index,timestamp,), wargs=(file,timestamp,))

            # Once adjustment has been performed, uncheck the box and set the 'adjusted' field to True.
            self.fileList[file][IS_ADJUSTED] = True 
            check = self.list.GetItem(index-1,0)
            box = check.GetWindow()
            box.SetValue(False)

        """Invoke the ffmpeg analysis routine and pipe the output to self._resultAnalyzeConsumer."""

    def _resultAnalyzeProducer(self, file, index):
        print "_resultAnalyzeProducer\n"
        print file
        print self
        print "target::::"
        print self.targetIL
        
        output_name = work_dir + "/LVLR.app/Contents/output_file_resultAnalyzeProducer.txt" ##
        output_file = open(output_name, 'w') ##
        proc = subprocess.call([ffmpegEXE, '-nostats', '-i', file, '-filter_complex', 'ebur128=peak=true+sample:framelog=verbose', '-f', 'null', '-'], bufsize=1, stdout=output_file, stderr=output_file)

        sys.stdout.flush()
        
        buffered = open(output_name, 'rU').read() ##made it = rather than +=
        sys.stdout.flush()
        #

        self.prologue = buffered.split('Press [q]')[0]    # Capture the beginning of the output information (which includes bitrate).

        
##test mono v. stereo

        channels = re.search(r'Hz, (.+?),', self.prologue)
        chVal = channels.group(1)
        print chVal
        print type(chVal)
        print "S v. M"
        

        if ((chVal == "mono") or (chVal == "1 channels")):
            print "mono!"
            self.fileList[file][IS_MONO] = True
            self.targetIL = -27
            print self.targetIL
            print self.fileList[file][FILE_NAME]

            
## put mono stuff back in here ##

        if ((chVal == "stereo") or (chVal == "2 channels")):
            print "stereo!"
            self.fileList[file][IS_MONO] = False
            self.targetIL = -24
            print self.targetIL
            print self.fileList[file][FILE_NAME]


        if not ((chVal == "mono") or (chVal == "1 channels") or (chVal == "stereo") or (chVal == "2 channels")):
            print "some other options!"
            self.fileList[file][IS_MONO] = False
            self.targetIL = -24
            print self.targetIL
        print "461"
        print self.fileList[file][IS_MONO]
       # self.summary = stdout.split('\n')[-16:]         # Capture the end of the output information.
#       self.summary = buffered.split('\n')[-16:]         # Capture the end of the output information.
        ##changed to deal with longer headers
        split_part = buffered.partition('Summary:\n')
        self.summary = str(split_part[2])
        result = self.prologue + ''.join(self.summary)    # Return both for processing. 

        item = self.list.GetItem(index,2)
        gauge = item.GetWindow()
        gauge.SetValue(50)

#
#        if not self.overwrite:
#            stereo_file = stem + "_stereo_" + timestamp + extension
#            mono_file = stem + "_mono_" + timestamp + extension

#        else: 
#            stereo_file = stem + "_stereo." + extension
#            mono_file = stem + "_mono." + extension
        
#        mono_file_full = dir + "/"+ mono_file
#        stereo_file_full = dir + "/"+ stereo_file
#        shutil.copy(file, mono_file_full)

#        if os.path.isfile(mono_file_full):
#            os.remove(mono_file_full) 
#        if os.path.isfile(stereo_file_full):
#            os.remove(stereo_file_full) 

        # Catch bad inputs and inform the user.
        badInput = re.search(r'Invalid data found when processing input', result) #will it get here without error?
        if badInput is not None:
            wx.CallAfter(self.OnBadInput,file)
        else:
            self.ProcessSummary(file, result, index)
        ##    
        
        
    def ProcessSummary(self, file, summary, i):
        """Process ffmpeg data and display it in the GUI."""
        errorFlag = False

        # Extract bitrate. 
        if not self.fileList[file][IS_ANALYZED]:
            bitrate = re.search(r'bitrate:\s(.+?) kb', summary) #changed from summary
            print "bitrate: "##
            print bitrate.group(1)
            if bitrate is not None:
                BR = bitrate.group(1)
                print "BR"
            else:
                BR = "n/a"
                errorFlag = True         
            self.fileList[file][BITRATE] = BR

        # Extract loudness range.
        #loudnessRange = re.search(r'LRA:\s(.+?) LU', summary)
        #if loudnessRange is not None:
        #    LRA = loudnessRange.group(1)
        #else:
        #    LRA = "n/a"
        #    errorFlag = True
        #self.list.SetStringItem(i,7,LRA)         
        #if i%3 == 0:
        #    self.fileList[file][LOUDNESS_RANGE] = LRA
        #else:
        #    self.fileList[file][LOUDNESS_RANGE_ADJ] = LRA

        # Extract integrated loudness. 
        ##print "blerg / problems second time through\n\n------\n"
        ##print summary
        print "\n\n-----"
        ##print self.summary

        print "\n\n-----"
        print type(summary)
        print type(self.summary)

        intloud = re.search(r'I:\s*(.+?) LUFS', summary)
        full_thing = intloud.group(0)
        print full_thing + "LUFS:: "
        print "|" + intloud.group(1)+"|"
        if intloud is not None:
            IL = intloud.group(1)
        else:
            IL = "n/a"
            errorFlag = True
        #IL = "30"
        #i = 0 ##testing
        ##test##
        #IL = "33"
        print "look::"
        print type(IL)


##



        if self.fileList[file][IS_MONO] == True:
            ILint = float(IL)
            ILtoShow = str(ILint + 3)
        else:
            ILtoShow = IL
            
        
        self.list.SetStringItem(i,4,ILtoShow)
        print "IL shown " + str(ILtoShow) + " & actual IL " + IL

        if i%3 == 0:
            self.fileList[file][INT_LOUD] = IL
        else:
            self.fileList[file][INT_LOUD_ADJ] = IL

        print "SUMMARY to USE"
        print type(summary)
        ##print summary
        # Extract true peak.
        truePeak = re.search(r'True peak:\s+Peak:\s+(.+?) dBFS', summary)
        #print "TP 0:" + truePeak.group(0)
        print "TP 1:"
        print truePeak.group(1)

        if truePeak is not None:
            TP = truePeak.group(1)
        else:
            TP = "n/a"
            errorFlag = True
        self.list.SetStringItem(i,5,TP)
        print "TP: \n"
        print TP ##
        if i%3 == 0:
            self.fileList[file][T_PEAK] = TP
        else:
            self.fileList[file][T_PEAK_ADJ] = IL

        # Extract sample peak.
        samplePeak = re.search(r'Sample peak:\s*Peak:\s*(.+?) dBFS', summary)
        print "SP 0:" + samplePeak.group(0)
        print "SP 1:" + samplePeak.group(1)

        if samplePeak is not None:
            SP = samplePeak.group(1)
            print "SP: "
            print SP
        else:
            SP = "n/a"
            errorFlag = True
        self.list.SetStringItem(i,6,SP)
        if i%3 == 0:
            self.fileList[file][S_PEAK] = SP
        else:
            self.fileList[file][S_PEAK_ADJ] = IL

        # Append time-stamped data to log file. 
        self.logfile.write(time.strftime("%d/%m/%Y: %H:%M:%S: "))
        self.logfile.write(file)
        if i%3 == 1:
            self.logfile.write(" (adjusted)")
        if errorFlag:
            self.logfile.write("\nThis process was aborted prematurely.")
        self.logfile.write("\nIntegrated Loudness: " + str(IL) + "\n")
        self.logfile.write("True Peak: " + str(TP) + "\n")
        #self.logfile.write("LRA: " + str(LRA) + "\n\n\n")
        self.logfile.write("********************************************************\n\n")
        ##

        ##
        # Notify users of any data-collection errors; if no errors are detected, flag the file as analyzed.
        if errorFlag:
            self.list.SetStringItem(i,3,"Error")
            print "Error!"
        else:
            self.fileList[file][IS_ANALYZED] = True
            print "Is _ Analyzed"

        # Determine whether the file conforms to specs.
        upperbound = self.targetIL + self.grace 
        lowerbound = self.targetIL - self.grace 


        if float(IL) > lowerbound and float(IL) < upperbound:
            valid = True
        else:
            valid = False
        if float(truePeak.group(1)) > self.targetPeak:
            valid = False

        # Notify the GUI of whether the file meets specs.
        if valid:
            self.list.SetStringItem(i,3,"Yes")
            item = self.list.GetItem(i,3)
            item.SetTextColour(wx.GREEN)    # ALICE: I can't make this color change work! Seems like it shouldn't be hard...
            self.list.SetItem(item)
            if i%3 == 0:
                self.fileList[file][MEETS_SPECS] = "Yes"
                check = self.list.GetItem(i,0)
                box = check.GetWindow()
#                box.SetValue(False)
 #               self.list.SetItem(check)
            else:
                self.fileList[file][MEETS_SPECS_ADJ] = "Yes"
        else:
            self.list.SetStringItem(i,3,"No")
            if i%3 == 0:
                self.fileList[file][MEETS_SPECS] = "No"
            else:
                self.fileList[file][MEETS_SPECS_ADJ] = "No"
 
    def _resultAdjustProducer(self, file, timestamp, index):
        """Invoke the ffmpeg adjust routine and pipe the output to __resultAdjustConsumer."""
 
        ###
        print self.fileList[file][FILE_NAME]
        print "target : \n\t"
        print self.targetIL
        print "is mp3 or mp2?"
        print self.fileList[file][IS_MP]
        print "is mono? \n\t"
        print self.fileList[file][IS_MONO]

        if self.fileList[file][IS_MONO] == True:
            self.targetIL = -27
        else:
            self.targetIL = -24
        
        print "target : \n\t"
        print self.targetIL
        
        
        output_name = work_dir + "/LVLR.app/Contents/output_file_resultAdjustProducer.txt" ##
        #output_file = open(output_name, 'w') ##

        output_name_second = work_dir + "/LVLR.app/Contents/output_file_resultAdjustProducer_second.txt" ##
        #output_file_second = open(output_name, 'w') ##

        
        # Extract file extension.
        dot = re.search("\.", file)
        extension = file[dot.end():]

        # Specify path of adjusted file based on config settings.
        (dir,just_file) = os.path.split(os.path.abspath(file))
        if not self.sameFold:
            dir = self.adjFileLoc
            fileNewFold = dir + SEPARATOR + just_file   #this could be part of the problem... maybe not a valid path?
        else:
            fileNewFold = file
        dot = re.search("\.", fileNewFold)
 
        # Convert mp3 files to wav before processing.
        # ALICE: This would be where you can add mp2 conversion as well. 
        
        print "EXT:: "
        print extension
        if ((extension == "mp3") or (extension == "mp2")):
            print "IS MP"
            old_ext = extension
            print "old extensions: " + old_ext

            self.fileList[file][IS_MP] = True    # Designate as mp3.
            print "yes, MP"
            extension = "wav"
            wav_file = fileNewFold[:dot.start()] + '.' + extension    # Name equivalent wav file.
            if os.path.isfile(wav_file):    # Remove any existing files of that name.
                os.remove(wav_file)
            output_file = open(output_name, 'w') ##proc = subprocess.call([ffmpegEXE, '-i', file, wav_file], bufsize = 1, stdout=output_file, stderr=output_file)
            sys.stdout.flush()
            output_file.close()
#            proc = subprocess.call([ffmpegEXE, '-i', file, wav_file], bufsize = 1, stdout=output_file, stderr=output_file)
            #stdout,stderr = proc.communicate()
            
            adjusted_MP = fileNewFold[:dot.start()] + "_adjusted." + old_ext    # Name final adjusted MP3 file.
            print adjusted_MP
            if os.path.isfile(adjusted_MP):    # Remove any existing files of that name.
                os.remove(adjusted_MP)

        # Define other helper files and remove any duplicates (i.e. permit overwrites). 
        ## overwriting ##
        #
        if self.overwrite:  
            start_file = fileNewFold[:dot.start()] + "_start." + extension
            intermed_file = fileNewFold[:dot.start()] + "_intermed." + extension
            adjusted_file = fileNewFold[:dot.start()] + "_adjusted." + extension   
        #if self.overwrite:  
        #    start_file = fileNewFold[:dot.start()] + "_start_" + timestamp + extension
        #    intermed_file = fileNewFold[:dot.start()] + "_intermed_" + timestamp + extension
        #    adjusted_file = fileNewFold[:dot.start()] + "_adjusted_" + timestamp + extension 
        else:
            start_file = fileNewFold[:dot.start()] + "_start_" + timestamp + extension
            intermed_file = fileNewFold[:dot.start()] + "_intermed_" + timestamp + extension
            adjusted_file = fileNewFold[:dot.start()] + "_adjusted_" + timestamp + extension 
        
        if os.path.isfile(start_file):
            os.remove(start_file) 
        if os.path.isfile(adjusted_file):
            os.remove(adjusted_file) 
        if os.path.isfile(intermed_file):
            os.remove(intermed_file)

        # Copy the original file to `start_file' to prevent modification of the original.
        shutil.copy(file, start_file) 

        print "int loud :: :: ::"
        print type(INT_LOUD)
        print INT_LOUD
        print type(self.fileList[file][INT_LOUD])
        print str(self.fileList[file][INT_LOUD])


        # Calculate gain shift and target peak.
        IL = float(self.fileList[file][INT_LOUD])
        TP = float(self.fileList[file][T_PEAK])
        gain = self.targetIL - IL
        newTruePeak = TP + gain

        print "newTP: " + str(newTruePeak) + "\t TP: " + str(TP) + "\t gain :" + str(gain)
        
        # Branch 1: integrated loudness is too low, upward gain shift required.
        if gain > 0:
            print "gain > 0"
        # Perform up to five extra rounds of gain shifting, to "nudge" finnicky files to the target value.
            count = 0
            direction = [False,False] #added by alice
            while (count < 5):
                print count
                # Branch 1A: no compression required, simply gain shift.
                if newTruePeak < self.targetPeak: 
                    #output_name_temp = work_dir + "/LVLR.app/Contents/output_file_resultAdjustProducer_indent.txt" ##
                    #output_file = open(output_name_temp, 'w') ##
                    print adjusted_file
                    print "\n --if -- \n\nadjusted file\n"
                    output_file = open(output_name_second, 'w') ##
                    proc = subprocess.call([ffmpegEXE, '-i', start_file, '-strict', '-2', '-af', 'volume=volume=' + str(gain) + 'dB:precision=fixed',  adjusted_file], bufsize=1, stdout=output_file, stderr=output_file)
                    
                    #stdout,stderr = proc.communicate() 
                    sys.stdout.flush()
                    output_file.close()
                # Branch 1B: begin iterative compression and gain shift.
                else:
                    j = 0
                    print "else"
                    print j
                    while (newTruePeak > self.targetPeak) and j < 4:    # Forestall infinite loops.
                        print "(newTruePeak > self.targetPeak)"
                        print newTruePeak
                        print self.targetPeak
                        # Perform round of compression.
                        offset = self.targetPeak - gain

                        #output_name_temp = work_dir + "/LVLR.app/Contents/output_file_resultAdjustProducer_indent2.txt" ##
                        #output_file = open(output_name_temp, 'w') ##
                        output_file = open(output_name, 'w') ##
                        proc = subprocess.call([ffmpegEXE, '-i', start_file, '-strict', '-2', '-af', 'compand=.00001:.5:-90/-90|-40/-40|-30/-30|-20/-20|-10/-10|-8/-8' + str(offset) + '/' + str(offset - 2) + '|-3/' + str(offset - 1) + '|-1/' + str(offset - 0.1) + '|0/' + str(offset) + ':0.01:0:0:0.01', intermed_file], bufsize=1, stdout=output_file, stderr=output_file)
                        sys.stdout.flush()
                        output_file.close()
#                        #stdout,stderr = proc.communicate()
#                        proc = subprocess.call([ffmpegEXE, '-i', start_file, '-strict', '-2', '-af', 'compand=.00001:.5:-90/-90|-40/-40|-30/-30|-20/-20|-10/-10|-8/-8' + str(offset) + '/' + str(offset - 2) + '|-3/' + str(offset - 1) + '|-1/' + str(offset - 0.1) + '|0/' + str(offset) + ':0.01:0:0:0.01', intermed_file], bufsize=1, stdout=output_file, stderr=output_file)
#                        #stdout,stderr = proc.communicate()

                        # Analyze the resulting file.
#                        proc  = subprocess.Popen([ffmpegEXE, '-nostats', '-i', intermed_file, '-filter_complex', 'ebur128=peak=true+sample', '-f', 'null', '-'], bufsize=1, stdout=output_file, stderr=output_file)
#                        #stdout,stderr = proc.communicate()

                        #output_name_temp = work_dir + "/LVLR.app/Contents/output_file_resultAdjustProducer_indent3.txt" ##
                        #output_file = open(output_name_temp, 'w') ##
                        print output_name
                        print "895"
                        output_file = open(output_name_second, 'w') ##
                        proc  = subprocess.call([ffmpegEXE, '-nostats', '-i', intermed_file, '-filter_complex', 'ebur128=peak=true+sample:framelog=verbose', '-f', 'null', '-'], bufsize=1, stdout=output_file, stderr=output_file)
                        sys.stdout.flush()
                        output_file.close()


                        ########

                        ########
                        #stdout,stderr = proc.communicate()
                            #
##
                        #bufferTry = open filePath, 
                        ## trying to make this work. 7.20
                        ##

#                        buf = open(output_name, 'rU').read() ##

                        buffered = open(output_name_second, 'rU').read() ##
                        print "\n\n\n"
                        print "------898a"
                        print output_name
                        print output_file                        
                        print type(buffered)
                        print buffered
                        print "\n\n\n"
##
##

                        print "------902"
                        split_part = buffered.partition('Summary:\n')
                        self.summary = str(split_part[2])
                        print type(self.summary)
                        print type(buffered)
                        print "1 / 2/ 0 "
                        print split_part[1]
                        print "1 / 2/ 0 "
                        print split_part[2]
                        print "1 / 2/ 0 "
                        print split_part[0]
                        print "\n\n"
                        ###buffered = open(filePath, 'r+').read() ##made it = rather than +=
                        print "buffered 922"
                        #summary = buffered ## take this out if using the buffered split below
                        
                        #summary = buffered.split('\n')[-16:]
                        
                        intloud = re.search(r'I:(.+?) LUFS',self.summary)
                        print type(intloud)
                        print intloud
                        intL = intloud.group(1)
                        print type(intL)
                        print intL
                        ## older version ## intloud = re.search(r'I:\s(.+?) LUFS', " ".join(buffered))




                        if intloud is not None:
                            intloud = float(intloud.group(1))
                            gain = self.targetIL - intloud
                        if intloud == None:
                            print "intloud is None"     
                            ###
                        print "self.targetIL"
                        print type(self.targetIL)
                        print "intloud"
                        print type(intloud)
                        print str(intloud)
                        print int(intloud)
                        print type(int(intloud))

                        truePeak = re.search(r'True peak:\s+Peak:\s(.+?) dBFS',self.summary)
                        if truePeak is not None:
                            truePeak = float(truePeak.group(1))
                        if truePeak == None:
                            print "truepeak is None"     
                            ###

                        # Perform requisite gain shift.
                        
                        output_file = open(output_name, 'w') ##

                        newGain = self.targetIL - intloud #OMW this will lead to problems if it's "n/a"
#                        proc = subprocess.Popen([ffmpegEXE, '-i', intermed_file, '-strict', '-2', '-af', 'volume=volume=' + str(newGain) + 'dB:precision=fixed',  adjusted_file], bufsize=1, stdout=output_file, stderr=output_file)
                        proc = subprocess.call([ffmpegEXE, '-i', intermed_file, '-strict', '-2', '-af', 'volume=volume=' + str(newGain) + 'dB:precision=fixed',  adjusted_file], bufsize=1, stdout=output_file, stderr=output_file)
                        sys.stdout.flush()
                        output_file.close()
    #Now here we're doing that extra round of analysis...
                        #stdout,stderr = proc.communicate()

                        # Analyze the resulting file (MAKE THIS A SEPARATE HELPER METHOD).
                        output_file = open(output_name, 'w') ##
                        proc  = subprocess.call([ffmpegEXE, '-nostats', '-i', adjusted_file, '-filter_complex', 'ebur128=peak=true+sample:framelog=verbose', '-f', 'null', '-'], bufsize=1, stdout=output_file, stderr=output_file)
                        sys.stdout.flush()
                        output_file.close()
                        #stdout,stderr = proc.communicate()
        #

                        #output_file = open(output_name, 'w') ##
                        buffered = open(output_name, 'rU').read() ##made it = rather than +=

                        print "buffered 845"
                        ##print buffered
                        print "buffered type: \n"
                        print type(buffered)
                        
                                #

                        ##other version of splitting
                        #summary = buffered.split('\n')[-16:]
                        split_part = buffered.partition('Summary:\n')
                        summary = str(split_part[2])
 
                        print "summary 989"
                        print summary

                        intloud = re.search(r'I:\s(.+?) LUFS', summary)
                        if intloud is not None:
                            intloud = float(intloud.group(1))
                        gain = self.targetIL - intloud

                        truePeak = re.search(r'True peak:\s+Peak:\s(.+?) dBFS', summary)
                        if truePeak is not None:
                            truePeak = float(truePeak.group(1))

                        # Calculate new true peak and rename files accordingly.
                        newTruePeak = truePeak
                        os.rename(adjusted_file, start_file) 
                        if os.path.isfile(intermed_file):
                            print "\n REMOVED!! \n"
                            os.remove(intermed_file)

                        j += 1

                    os.rename(start_file, adjusted_file)

                # Process the output.
                output_file = open(output_name, 'w') ##
                proc = subprocess.call([ffmpegEXE, '-nostats', '-i', adjusted_file, '-filter_complex', 'ebur128=peak=true+sample:framelog=verbose', '-f', 'null', '-'], bufsize=1, stdout=output_file, stderr=output_file)
                #stdout,stderr = proc.communicate()
                sys.stdout.flush()
                output_file.close()
                buffered = open(output_name, 'rU').read() ##made it = rather than +=
                #filePath.close()
                print "------1088"
                print output_name
                print output_file                        
                print type(buffered)
                print buffered


                #summary = buffered.split('\n')[-16:]

                split_part = buffered.partition('Summary:\n')
                summary = str(split_part[2])
                print "1057"
                print summary

                intloud = re.search(r'I:\s(.+?) LUFS', summary)
                print intloud

                gainDiff = 0 ##
                
                if intloud is not None:
                    print "NOT NONE\n\n"
                    print type(self.targetIL)
                    print self.targetIL
                    print type(intloud)
                    print intloud

                    intloud = float(intloud.group(1))
                    gainDiff = self.targetIL - intloud

                if gainDiff == 0:
                    break
                else:
                    if gainDiff < 0:
                        direction[0] = True
                    else:
                        direction[1] = True
                    count += 1
                    print count
                    print direction
                    if direction[0] and direction[1]:
                        gainDiff = gainDiff/3.0
                        print gainDiff
                    gain = gain + gainDiff
                    if os.path.isfile(intermed_file):
                        os.remove(intermed_file)
                    if count == 4 and os.path.isfile(adjusted_file):
                        os.remove(adjusted_file)

        # Branch 2: integrated loudness is too high, downward gain shift required.
        else:
        # Perform up to five extra rounds of gain shifting, to "nudge" finnicky files to the target value.
            count = 0
            direction = [False,False]
            while (count < 5):
                # Perform downward gain shift.
                output_file = open(output_name, 'w') ##
                proc = subprocess.call([ffmpegEXE, '-i', start_file, '-strict', '-2', '-af', 'volume=volume=' + str(gain) + 'dB:precision=fixed',  intermed_file], bufsize=1, stdout=output_file, stderr=output_file)
                sys.stdout.flush()
                output_file.close()
                #stdout,stderr = proc.communicate()

                # Branch 2A: Perform compression if required. 
                if newTruePeak > self.targetPeak: #but... that actually will never be the case, right??
                    output_file = open(output_name, 'w') ##
                    proc2 = subprocess.call([ffmpegEXE, '-i', intermed_file, '-strict', '-2', '-af', 'compand=.00001|.00001:.5|.5:-90/-90|-4/-4|-3.2/-3.3|-3.1/-3.2|0/-3.1:0.01:0:0:0.01', adjusted_file], bufsize=1, stdout=output_file, stderr=output_file)
                    sys.stdout.flush()
                    output_file.close()
                    #stdout, stderr = proc2.communicate() 

                # Branch 2B: Otherwise, change file names accordingly.
                else:
                    print "\nelse!! \n"
                    
                    print "\n\n" + intermed_file
                    
                    print "\n\n" + adjusted_file

                    ##os.remove(adjusted_file)

                    print "\n\n" + adjusted_file

                    os.rename(intermed_file, adjusted_file)



                # Process the output.
                output_file = open(output_name, 'w') ##
                proc = subprocess.call([ffmpegEXE, '-nostats', '-i', adjusted_file, '-filter_complex', 'ebur128=peak=true+sample:framelog=verbose', '-f', 'null', '-'], bufsize=1, stdout=output_file, stderr=output_file)
                sys.stdout.flush()
                output_file.close()
                #stdout,stderr = proc.communicate()  


##
                 ##
                buffered = open(output_name, 'rU').read() ##made it = rather than +=
                #filePath.close()

                print "buffered 1140"
                ##print buffered
                print "buffered type: \n"
                print type(buffered)
                
                #
                ##other version ## summary = buffered.split('\n')[-16:]
                split_part = buffered.partition('Summary:\n')
                summary = str(split_part[2])
 

                intloud = re.search(r'I:\s(.+?) LUFS', summary)
                if intloud is not None:
                    intloud = float(intloud.group(1))
                    gainDiff = self.targetIL - intloud

                if gainDiff == 0:
                    break
                else:
                    if gainDiff < 0:
                        direction[0] = True
                    else:
                        direction[1] = True
                    count += 1
                    print count
                    print direction
                    if direction[0] and direction[1]:
                        gainDiff = gainDiff/2.0
                    print gainDiff
                    gain = gain + gainDiff
                    if os.path.isfile(intermed_file):
                        os.remove(intermed_file)
                    if count == 4 and os.path.isfile(adjusted_file):
                        os.remove(adjusted_file)


 
        # Analyze output.
        
        output_file = open(output_name, 'w') ##
        proc = subprocess.call([ffmpegEXE, '-nostats', '-i', adjusted_file, '-filter_complex', 'ebur128=peak=true+sample:framelog=verbose', '-f', 'null', '-'], bufsize=1, stdout=output_file, stderr=output_file)
        sys.stdout.flush()
        output_file.close()
        #stdout,stderr = proc.communicate()  
        ###


        buffered = open(output_name, 'rU').read() ##made it = rather than +=
        print "buffered 1190"
        
        print "buffered type: \n"
        print type(buffered)
        split_part = buffered.partition('Summary:\n')
        summary = str(split_part[2])
 
    
        intloud = re.search(r'I:\s(.+?) LUFS', summary)
        if intloud is not None:
            intloud = float(intloud.group(1))
            gain = self.targetIL - intloud
#Do I actually need this anymore????

        # If the original file was an mp3, convert the intermediate wav file to an mp3 using the appropriate bitrate.
        if self.fileList[file][IS_MP]:
            bitrateParam = self.GetBitrateParam(self.fileList[file][BITRATE])
            
            print "BITRATE to go back to :: "
            print bitrateParam
            print adjusted_MP
            output_file = open(output_name, 'w')
            if (abs(bitrateParam - 128) < 10):
                bitrateParam = 128
            if (abs(bitrateParam - 256) < 10):
                bitrateParam = 256

            br_to_use = str(bitrateParam) + 'k'
            print br_to_use
#            proc = subprocess.call([ffmpegEXE,'-i', adjusted_file, '-b:a', str(bitrateParam), adjusted_MP])
            proc = subprocess.call([ffmpegEXE,'-i', adjusted_file, '-b:a', br_to_use, adjusted_MP])
 
#            proc = subprocess.call([ffmpegEXE,'-i', adjusted_file, '-codec:a', 'libmp3lame', '-qscale:a', str(bitrateParam), adjusted_MP])

            sys.stdout.flush()
            output_file.close()
            #stdout,stderr = proc.communicate()

            output_file = open(output_name, 'w') ##
            proc = subprocess.call([ffmpegEXE, '-nostats', '-analyzeduration', '2147483647', '-probesize', '2147483647', '-i', adjusted_MP, '-filter_complex', 'ebur128=peak=true+sample:framelog=verbose', '-f', 'null', '-'], bufsize=1, stdout=output_file, stderr=output_file)
#            proc = subprocess.call([ffmpegEXE, '-nostats', '-i', adjusted_MP, '-filter_complex', 'ebur128=peak=true+sample:framelog=verbose', '-f', 'null', '-'], bufsize=1, stdout=output_file, stderr=output_file)
            sys.stdout.flush()
            output_file.close()
            if os.path.isfile(adjusted_file):
                os.remove(adjusted_file)#one thing to check

        else:          
            output_file = open(output_name, 'w') ##
            proc = subprocess.call([ffmpegEXE, '-nostats', '-i', adjusted_file, '-filter_complex', 'ebur128=peak=true+sample:framelog=verbose', '-f', 'null', '-'], bufsize=1, stdout=output_file, stderr=output_file)
            sys.stdout.flush()
            output_file.close()
        #stdout,stderr = proc.communicate()  
        #
        
#        buffered = open(filePath, 'rU').read() ##made it = rather than +=
        buffered = open(output_name, 'rU').read()
        #filePath.close()
        ##print buffered ##made it = rather than +=
 
        print "buffered 1033"

        print "buffered type: \n"
        print type(buffered)
        print buffered

        print "buffer:\n"

        print "\\\\\|||||////"
        #

        #self.summary = buffered.split('\n')[-16:]
        split_part = buffered.partition('Summary:\n')
        self.summary = str(split_part[2])
 
        # Clean up any loose files. 
        if os.path.isfile(start_file):
            os.remove(start_file)
        if os.path.isfile(intermed_file):
            os.remove(intermed_file)
        if self.fileList[file][IS_MP]:  #(OMW: Check to make sure this doesn't break anything!!)
            if os.path.isfile(wav_file):
                os.remove(wav_file)

        result = ''.join(self.summary)
        print "result\n\n::1227\n"
        print result
        ##index = 1     # arbitrary number: I chose 1 because it corresponds to the adjust row of the first loaded file.
        print "index" + str(index)
        self.ProcessSummary(file, result, index) 
        item = self.list.GetItem(index,2)
        gauge = item.GetWindow()
        gauge.SetValue(50)
        print "gauge type: "
        print type(gauge)
        
    def GetBitrateParam(self, bitrate):
        """Convert bitrate to the appropriate libmp3lame parameter. (Note that for boundary cases, 
           we have chosen to air on the side of a higher bitrate. https://trac.ffmpeg.org/wiki/Encode/MP3)"""
        
        print "BitRate :: "
        print bitrate
        print type(bitrate)
        bitrateString = bitrate
        bitrate = int(bitrateString)
        print type(bitrate)
        print bitrate
        return bitrate
        """
        if bitrate > 220:
            return 0
        elif bitrate > 190:
            return 1
        elif bitrate > 170:
            return 2
        elif bitrate > 150:
            return 3
        elif bitrate > 140:
            return 4
        elif bitrate > 120:
            return 5
        elif bitrate > 100:
            return 6
        elif bitrate > 80:
            return 7
        elif bitrate > 70:
            return 8
        elif bitrate > 45:
            return 9
        else:
            return 0 """


    def OnLoadFile(self, event):
       """Load a file selection dialog."""
       print "OnLoadFile (self, event)" + str(self) + "::" +  str(event)
       dlg = wx.FileDialog(self, "Choose a file:", os.getcwd(), "", "*.*", wx.OPEN | wx.FD_MULTIPLE)
       dlg.SetWildcard(self.wildcard)     # Establish allowed file types.
       if dlg.ShowModal() == wx.ID_OK:
           for file in dlg.GetPaths():
               self.AddToList(file)
               print "AddToList(file)" + str(file)
       dlg.Destroy()
       self.Render()


    def OnLoadFolder(self, event):
       """Load a folder selecton dialog."""

       dlg = wx.DirDialog(self, "Choose a directory:", style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
       if dlg.ShowModal() == wx.ID_OK:
           path = dlg.GetPath()
           for file in os.listdir(path):
               self.AddToList(path + SEPARATOR + file)   # Separator depends on the OS. 
       dlg.Destroy()
       self.Render()


    def AddToList(self, file):
       """Add a file to the queue."""
       print "AddToList self, file" + str(self) + "::" + str(file)
       # Isolate the file extension.
       rawfilename = os.path.basename(file)
       dot = re.search("\.(?=[^.]*$)",rawfilename)
       if dot:
          extension = rawfilename[dot.end():]
       else:
          extension = "dummyExt"    # ALICE: I have yet to see this error... But it probably should be accounted for somehow.

       # Add files that have an appropriate extension and have not been previously added.
       if not file in self.fileList and extension in self.allowedExtensions:

          # The main file storage data structure: a dictionary, indexed by file name, that stores the following values:
          #     file name, meets specs?, IL, TP, SP, LRA, bitrate, isRendered, isAnalyzed, isAdjusted, isMP3, meets specs 
          #     after adjustment?, IL_adjusted, TP_adjusted, SP_adjusted, LRA_adjusted isBad.
          #     ALICE: We could make this an 18-tuple and also store sample rate.
          self.fileList[file] = [file,'','','','','','',False,False,False,False,'','','','','',False, False] 
          print "fileList[file]" + str(file) + "\n\t" + str(self.fileList[file])
 
    def Render(self):
       """Display file list."""
       print "RENDER"

       # If the file list is not empty, enable buttons.
       if self.fileList:
          self.sel.Enable()
          self.des.Enable()
          self.rem.Enable()
          self.ana.Enable()
          self.adj.Enable()

       # Add file to the window if it hasn't been previously rendered.   
       for file in self.fileList:
          entry = self.fileList[file]

          if not entry[IS_RENDERED]:  
             index = self.list.InsertStringItem(sys.maxint, '')
             print "index::" + str(index)
             (dir,just_file) = os.path.split(os.path.abspath(file))
             self.list.SetStringItem(index, 1, just_file)
             self.list.SetStringItem(index, 3, entry[MEETS_SPECS])
             posit = self.list.GetItemPosition(index)
             self.list.SetStringItem(index, 4, entry[INT_LOUD])
             self.list.SetStringItem(index, 5, entry[T_PEAK])
             self.list.SetStringItem(index, 6, entry[S_PEAK])
             #self.list.SetStringItem(index, 7, entry[LOUDNESS_RANGE])
       
             # Insert and automatically select checkboxes.
             check = self.list.GetItem(index,0)
             box = wx.CheckBox(self.list, -1, size=(20,20),pos=posit)   # The checkbox needed to be forced to a reasonable location. 
             if entry[IS_ADJUSTED]: 
                 box.SetValue(False)
             else:
                 box.SetValue(True)
             check.SetWindow(box, wx.ALIGN_CENTRE)
             self.list.SetItem(check)

             # Insert progress bars (initialized to zero). 
             item = self.list.GetItem(index,2)
             item._mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT | ULC.ULC_MASK_FONTCOLOUR
             width = self.list.GetColumnWidth(1)
             self.gauge = wx.Gauge(self.list,-1,range=50,size=(width,15),style=wx.GA_HORIZONTAL | wx.GA_SMOOTH)
             if entry[IS_ANALYZED]:
                 self.gauge.SetValue(50)
             else:
                 self.gauge.SetValue(0)
             item.SetWindow(self.gauge, wx.ALIGN_CENTRE)
             self.list.SetItem(item) 

             # Leave two spaces between each entry for adjustment and readability.
             adjustrow = self.list.InsertStringItem(sys.maxint, '')   
             if entry[IS_ADJUSTED]:
                 dot = re.search("\.", just_file)
                 extension = just_file[dot.end():]
                 adjusted_file = just_file[:dot.end()-1] + "_adjusted." + extension
                 self.list.SetStringItem(adjustrow, 1, adjusted_file)
                 self.list.SetStringItem(adjustrow, 3, entry[MEETS_SPECS_ADJ])
                 self.list.SetStringItem(adjustrow, 4, entry[INT_LOUD_ADJ])
                 self.list.SetStringItem(adjustrow, 5, entry[T_PEAK_ADJ])
                 self.list.SetStringItem(adjustrow, 6, entry[S_PEAK_ADJ])
                 self.list.SetStringItem(adjustrow, 7, entry[LOUDNESS_RANGE_ADJ])

                 item = self.list.GetItem(adjustrow,2)
                 item._mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_FORMAT | ULC.ULC_MASK_FONTCOLOUR
                 width = self.list.GetColumnWidth(1)
                 self.gauge = wx.Gauge(self.list,-1,range=50,size=(width,15),style=wx.GA_HORIZONTAL | wx.GA_SMOOTH)
                 self.gauge.SetValue(50)
                 item.SetWindow(self.gauge, wx.ALIGN_CENTRE)
                 self.list.SetItem(item) 

             # ALICE: Do these all-caps flags give you the impression that I'm shouting at you? My apologies...
             self.list.InsertStringItem(sys.maxint, '')
             entry[IS_RENDERED] = True     # Flag the file as rendered

       self.UpdateIndexMap()


    def UpdateIndexMap(self):
        """Reset the index map to reflect any newly added files."""

        self.indexMap = []
        for file in self.fileList:
            self.indexMap.append(file) 


    def OnSelectAll(self, event):
        """Check all boxes in the file list."""

        num = self.list.GetItemCount()
        for i in range(num):
            if i%3 == 0:
                check = self.list.GetItem(i,0)
                box = check.GetWindow()
                box.SetValue(True)
                self.list.SetItem(check)
           

    def OnDeselectAll(self, event):
        """Uncheck all boxes in the file list."""

        num = self.list.GetItemCount()
        for i in range(num):
            if i%3 == 0:
                check = self.list.GetItem(i,0)
                box = check.GetWindow()
                box.SetValue(False)
                self.list.SetItem(check)


    def OnRemove(self, event):
        """Remove selected files from the file list."""

        toDelete = []
        self.buffer_list = []    # Store recently deleted files
        num = self.list.GetItemCount()

        # Compile list of files selected for deletion. 
        for i in range(num):
           if i%3 == 0:
              check = self.list.GetItem(i,0)
              box = check.GetWindow()           
              if box.GetValue():
                 toDelete.append(self.indexMap[i/3])
              self.fileList[self.indexMap[i/3]][IS_RENDERED] = False 
              
        # Pop files from the fileList (adding them to a buffer for safe-keeping) and re-render. 
        for name in toDelete:
           self.buffer_list.append(self.fileList.pop(name))
        self.list.DeleteAllItems()
        self.Render()
        self.und.Enable() 
 
        
    def OnUndo(self, event):
        """Restore recently deleted files."""

        for recentlyDeleted in self.buffer_list: 
            self.fileList[recentlyDeleted[FILE_NAME]] = recentlyDeleted
        self.Render()
        self.und.Disable()


class FileDrop(wx.FileDropTarget):
    """Implement drag-and-drop functionality."""

    def __init__(self, window, parent):
        wx.FileDropTarget.__init__(self)
        self.window = window
        self.parent = parent

    def OnDropFiles(self, x, y, filenames):
        """If possible, drop selected files into main window."""

        try: 
           for file in filenames: 
              mypath = os.path.basename(file)
              self.parent.AddToList(file)
           self.parent.Render()
        except IOError, error:
           dlg = wx.MessageDialog(None, 'Error opening file\n' + str(error))
           dlg.ShowModal()


class LoudnessInfoDialog(wx.Dialog):
    """Display information and links relating to loudness standards."""

    def __init__(self, parent):
        wx.Dialog.__init__(self, None, title="Loudness Standards Explained", size=(350,300))
        hwin = HTMLWindow(self, -1, size=(400,400))
        infoText = """<p> Loudness levels recommended by the EBU for broadcasting are currently fixed at <b>-24 LUFS</b> (integrated) and <b>-2 LUFS</b> (peak). See <a href="www.tcelectronic.com/loudness/loudness-explained/">EBU Loudness Standards</a></p> for further details."""
        hwin.SetPage(infoText)
        btn = hwin.FindWindowById(wx.ID_OK)
        self.CentreOnParent(wx.BOTH)
        self.SetFocus()
        hwin.Show()
            

class HTMLWindow(wx.html.HtmlWindow):
    """Support the creation of a dialog box with html links."""

    def __init__(self, parent, id, size=(600,400)):
        wx.html.HtmlWindow.__init__(self,parent, id, size=size)
   
    def OnLinkClicked(self, link):
        wx.LaunchDefaultBrowser(link.GetHref())


class LabsInfoDialog(wx.Dialog):
    """Display information about NPR Labs."""

    def __init__(self, parent):
        wx.Dialog.__init__(self, None, title="NPR Labs", size=(250,300))
        hwin = HTMLWindow(self, -1, size=(400,200))
        infoText = """<p> NPR Labs is the only non-profit organization for broadcast technology research and development in America.Based in Washington DC, NPR Labs produces cutting-edge tools and technologies, in addition to conducting sophisticated psychoacoustic experiments. Visit <a href="www.nprlabs.org">NPR Labs</a></p> for more information."""
        hwin.SetPage(infoText)
        btn = hwin.FindWindowById(wx.ID_OK)
        self.CentreOnParent(wx.BOTH)
        self.SetFocus()
        hwin.Show()

class SettingsDialog(wx.Dialog):
    """Allow the user to customize their preferences.""" 

    def __init__(self, parent):
        wx.Dialog.__init__(self, None, title="Preferences", size=(450,500))
        self.parent = parent
        
        # Set general preferences (file locations, overwrite settings, etc).
        wx.StaticBox(self, -1, 'General Settings', pos=(5,5), size=(440, 240))        
        # ALICE: By commenting out every third line or so below, I've made it so that toggling values
        #    in the preferences menu does NOT actually change the official session settings. Uncommenting
        #    these will bind the widgets to functions which do change those universal values.
        
        wx.StaticText(self, -1, 'Adjusted file placement:', (15,30))
        self.sameFold = wx.RadioButton(self, -1, 'Place adjusted files in the same folder as the original file.', pos=(30,55))        
        self.sameFold.SetValue(self.parent.sameFold)
        # self.Bind(wx.EVT_RADIOBUTTON, self.OnSameFold, id=self.sameFold.GetId())

        self.diffFold = wx.RadioButton(self, -1, 'Place adjusted files in separate folder.', pos=(30,80))
        #self.diffFold.SetValue(self.parent.diffFold)
        # self.Bind(wx.EVT_RADIOBUTTON, self.OnDiffFold, id=self.diffFold.GetId())
        
        self.adjFileLoc = wx.DirPickerCtrl(self, -1,self.parent.adjFileLoc,pos=(15,110), size=(415,-1))
        self.adjFileLoc.Disable()
        # self.Bind(wx.EVT_DIRPICKER_CHANGED, self.OnAdjFileLoc, id=self.adjFileLoc.GetId())

        wx.StaticText(self, -1, 'Log file placement:', (15,150))
        self.logFileLoc = wx.DirPickerCtrl(self, -1,self.parent.logFileLoc, pos=(15,170), size=(415,-1))
        # self.Bind(wx.EVT_DIRPICKER_CHANGED, self.OnLogFileLoc, id=self.logFileLoc.GetId())

        self.overwrite = wx.CheckBox(self, -1, 'Overwrite existing adjusted files?', (15,215))
        self.overwrite.SetValue(self.parent.overwrite)  
        # self.Bind(wx.EVT_CHECKBOX, self.OnOverwrite, id=self.overwrite.GetId())      

        # Set advanced preferences (loudness targets).
        wx.StaticBox(self, -1, 'Advanced Settings (NOT FOR PUBLIC RADIO USE)', pos=(5,260), size=(440, 140))

        wx.StaticText(self, -1, 'Target Integrated Loudness', (15, 285))
        self.intloudSpin = wx.SpinCtrl(self, -1, min=-40, max=0, initial=-24, size=(60,-1), pos=(250,285))
        self.intloudSpin.SetValue(-24)
        # self.Bind(wx.EVT_SPINCTRL, self.OnIntLoudSpin, id=self.intloudSpin.GetId())
        if not self.parent.advancedAccess:
            self.intloudSpin.Disable()

        wx.StaticText(self, -1, 'Target Peak Loudness', (15, 325))
        self.peakSpin = wx.SpinCtrl(self, -1, min=-40, max=0, initial = -2, size=(60,-1), pos=(250,325))
        self.peakSpin.SetValue(-2)
        # self.Bind(wx.EVT_SPINCTRL, self.OnPeakSpin, id=self.peakSpin.GetId())
        if not self.parent.advancedAccess:
            self.peakSpin.Disable()

        wx.StaticText(self, -1, 'Allowed margin of error for IL', (15, 365))
        self.graceSpin = wx.SpinCtrl(self, -1, min=0, max=5, initial = 2, size=(60,-1), pos=(250, 365))
        self.graceSpin.SetValue(2)
        # self.Bind(wx.EVT_SPINCTRL, self.OnGraceSpin, id=self.graceSpin.GetId())
        if not self.parent.advancedAccess:
            self.graceSpin.Disable()


        self.close = wx.Button(self, -1, 'Close', pos=(70, 440), size=(100,-1))
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=self.close.GetId()) 

        self.apply = wx.Button(self, -1, 'Apply', pos=(20, 410), size=(100, -1))
        self.Bind(wx.EVT_BUTTON, self.OnApply, id=self.apply.GetId())

        self.defaults = wx.Button(self, -1, 'Restore Defaults', pos=(220, 440), size=(150, -1))
        self.Bind(wx.EVT_BUTTON, self.OnRestoreDefaults, id=self.defaults.GetId())

        self.save = wx.Button(self, -1, 'Save Settings for Future Session', pos=(170,410), size=(250,-1))
        self.Bind(wx.EVT_BUTTON, self.OnSaveSettings, id=self.save.GetId())

        self.Centre()
        self.ShowModal()
        self.Destroy()


    def OnSameFold(self, event):
        self.adjFileLoc.Disable()

    def OnDiffFold(self, event):
        self.adjFileLoc.Enable()

    def OnLogFileLoc(self, event):
        self.parent.logFileLoc = self.logFileLoc.GetTextCtrlValue()

    def OnAdjFileLoc(self, event):
        self.parent.adjFileLoc = self.adjFileLoc.GetTextCtrlValue()

    def OnOverwrite(self, event):
        self.parent.overwrite = self.overwrite.GetValue() 

    def OnIntLoudSpin(self, event):
        self.parent.targetIL = self.intloudSpin.GetValue() 

    def OnPeakSpin(self, event):
        self.parent.targetPeak = self.peakSpin.GetValue() 

    def OnGraceSpin(self, event):
        self.parent.grace = self.graceSpin.GetValue() 

    def OnRestoreDefaults(self, event):
        """Restore default settings (for current session)."""

        self.parent.targetPeak = TARGET_PEAK_DEFAULT
        self.peakSpin.SetValue(TARGET_PEAK_DEFAULT)

        self.parent.targetIL = TARGET_IL_DEFAULT
        self.intloudSpin.SetValue(TARGET_IL_DEFAULT)

        self.parent.grace = GRACE_DEFAULT
        self.graceSpin.SetValue(GRACE_DEFAULT)

        self.parent.overwrite = OVERWRITE_DEFAULT
        self.overwrite.SetValue(OVERWRITE_DEFAULT)

        self.parent.sameFold = SAME_FOLDER_DEFAULT
        self.sameFold.SetValue(SAME_FOLDER_DEFAULT)   

        self.parent.logFileLoc = LOG_FILE_LOC_DEFAULT
        self.logFileLoc.SetPath(LOG_FILE_LOC_DEFAULT)

        self.parent.adjFileLoc = ADJ_FILE_LOC_DEFAULT
        self.adjFileLoc.SetPath(ADJ_FILE_LOC_DEFAULT)

    def OnSaveSettings(self, event):
        """Write current preferences to the config file for later retrieval."""

        self.parent.config['TARGET_IL'] = str(self.intloudSpin.GetValue())
        self.parent.config['TARGET_PEAK'] = str(self.peakSpin.GetValue())
        self.parent.config['GRACE'] = str(self.graceSpin.GetValue())
        self.parent.config['OVERWRITE'] = self.overwrite.GetValue()
        self.parent.config['SAME_FOLDER'] = self.sameFold.GetValue()
        self.parent.config['DIFF_FOLDER'] = self.diffFold.GetValue()
        self.parent.config['ADJ_FILE_LOC'] = str(self.adjFileLoc.GetTextCtrlValue())
        self.parent.config['LOG_FILE_LOC'] = str(self.logFileLoc.GetTextCtrlValue())

        self.parent.WriteConfig()

        dlg = wx.MessageDialog(self, "Settings saved to configuration file.", "Settings saved.", style=wx.OK|wx.CENTRE)
        dlg.ShowModal()
        dlg.Destroy()

    def OnClose(self, event): 
        """Preferences menu closes without settings being changed."""

        self.Close()

    def OnApply(self, event):
        """Apply user preferences to the current session."""

        self.parent.targetPeak = self.peakSpin.GetValue()  
        self.parent.targetIL = self.intloudSpin.GetValue()
        self.parent.grace = self.graceSpin.GetValue()
        self.parent.overwrite = self.overwrite.GetValue()
        self.parent.sameFold = self.sameFold.GetValue()
        self.parent.adjFileLoc = self.adjFileLoc.GetTextCtrlValue()
        self.parent.logFileLoc = self.logFileLoc.GetTextCtrlValue()
 
        self.Close()

def str2bool(v):
   """Convert the string 'True' to its boolean equivalent."""
   return v in ("True")



# Build the Leveler application (*drum roll*). 

MainWindow(None, -1, 'NPR Leveler')
app.MainLoop()