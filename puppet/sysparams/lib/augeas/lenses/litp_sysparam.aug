module LITP_Sysparam =

  let eol = Util.eol
  let indent = Util.indent
  let key_re = /[\/A-Za-z0-9_.-]+/
  let eq = del /[ \t]*=[ \t]*/ " = "
  let value_re = /[^ \t\n](.*[^ \t\n])?/

  let comment = [ indent . label "#comment" . del /[#;][ \t]*/ "# "
        . store /([^ \t\n].*[^ \t\n]|[^ \t\n])/ . eol ]

  let empty = Util.empty

  let value = [ label "value" . store value_re ]
  let kv = [ indent . label "sysparam" . store key_re . eq . value . eol ]

  let lns = (empty | comment | kv) *

