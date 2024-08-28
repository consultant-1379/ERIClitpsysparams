define sysparams::param ($key, $value, $ensure = undef) {
    include "::sysparams"

    if $ensure == "present" {
        $value_space_compacted = regsubst($value, "\s{2,}", " ", 'G')
        exec { "sysctl-${title}":
            command     => "/sbin/sysctl -w ${key}='${value_space_compacted}' && /sbin/sysctl ${key} | sed 's/\t/ /g' | grep ' = ${value_space_compacted}$'",
            before      => Augeas["${key}-set"],
            unless	=> "/sbin/sysctl -e ${key} | sed -e 's/^.*= //' -e 's/\\s/ /g' | grep -q -- \"${value_space_compacted}\""
        }
        augeas { "${key}-set":
            lens => "LITP_Sysparam.lns",
            incl => "/etc/sysctl.conf",
            changes => [
                "set /files/etc/sysctl.conf/sysparam[. = '$key' ] $key",
                "set /files/etc/sysctl.conf/sysparam[. = '$key' ]/value '${value_space_compacted}'"
            ],
            onlyif   => "match /files/etc/sysctl.conf/sysparam[. = $key ]/value != ['${value_space_compacted}']",
            require     => File['/etc/sysctl.conf']
        }
    } elsif $ensure == "absent" {
        augeas { "${key}-remove":
            lens => "LITP_Sysparam.lns",
            incl => "/etc/sysctl.conf",
            changes => "rm /files/etc/sysctl.conf/sysparam[. = \"$key\" ]",
            require     => File['/etc/sysctl.conf']
        }
    }
}
