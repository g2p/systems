# vim: set fileencoding=utf-8 sw=2 ts=2 et :

def register():
  import aptitudepackage
  aptitudepackage.register()
  import command
  command.register()
  import file
  file.register()
  import pythoncode
  pythoncode.register()
  import user
  user.register()


