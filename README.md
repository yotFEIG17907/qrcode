# Music Player Server

Organized with multiple packages in a single repo. See
this (https://stackoverflow.com/questions/51296179/how-do-i-build-multiple-wheel-files-from-a-single-setup-py)[https://stackoverflow.com/questions/51296179/how-do-i-build-multiple-wheel-files-from-a-single-setup-py]

Raspberry PI development. PyCharm supports report development via ssh; this uses PyCharm basically as a remote editor, like using an SFTP plugin with Notepad++. But even better than that it can configure a remote python interpreter as the interpreter for the project and then it becomes possible to run and debug the applicaiton via PyCharm when it is running on the remote system, e.g. a Raspberry PI. And this also means that packages that are specific to the PI can be used in the complication so Auto-Completion with those packages becomes possible. It is tricky to set up, see this
[Configuring a remote interpreter in PyCharm](https://www.jetbrains.com/help/pycharm/configuring-remote-interpreters-via-ssh.html#ssh)
