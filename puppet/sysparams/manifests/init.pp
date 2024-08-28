class sysparams {
    file { "/etc/sysctl.conf":
        ensure => file
    }
}
