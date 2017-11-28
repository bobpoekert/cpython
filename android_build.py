import os, sys
from subprocess import call, check_output

android_home = '/home/bob/android'
ndk_home = '%s/android-ndk-r16' % android_home

host_arch = check_output(['gcc', '-dumpmachine']).strip()

call(['mkdir', '-p', 'build/'])

archs = [
        ('arm',  'arm-linux-androideabi', 'arm-linux-androideabi', 'armeabi-v7a'),
        ('arm64',  'aarch64-linux-android', 'aarch64-linux-android', 'armeabi'),
        ('mips',  'mipsel-linux-android', 'mipsel-linux-android', 'mips'),
        ('x86',  'x86', 'i686-linux-android', 'x86')]

def ssl_select_build_arch(aname):
    if 'arm64' in aname:
        return 'linux-aarch64'
    if 'v7a' in aname:
        return 'android-armv7'
    if aname == 'mips':
        return 'android-mips'
    if 'arm' in aname:
        return 'android'
    if 'x86' in aname:
        return 'android-x86'
    if 'x86_64' in aname:
        return 'linux-x86_64'
    return 'linux-armv4'

openssl_dir = os.path.abspath('./openssl/openssl-1.0.2h/')

def build_openssl(env, arch_name, gnu_arch_name, gcc_name, lib_dir):
    env = dict(**env)
    del env['CROSS_COMPILE']
    sh = lambda args: call(args, env=env, cwd=openssl_dir)
    ssl_arch = ssl_select_build_arch(arch_name)
    sh(['perl', 'Configure', 'no-shared', 'no-dso', 'no-krb5', ssl_arch])
    sh(['make', 'clean'])
    sh(['make', '-j5', 'depend'])
    sh(['make', '-j5'])
    sh(['make', 'install'])

def build(arch_name, gnu_arch_name, gcc_name, android_name):
    build_dir = os.path.abspath('./build/%s' % arch_name)
    call(['mkdir', '-p', './target/%s' % android_name])
    env = dict(**os.environ)
    env['CROSS_COMPILE'] = '%s-4.9' % gnu_arch_name
    env['CC'] = '%s-gcc' % gcc_name
    env['CXX'] = '%s-g++' % gcc_name
    env['PATH'] = '%s/toolchains/%s-4.9/prebuilt/linux-x86_64/bin:%s' % (ndk_home, gnu_arch_name, env.get('PATH', ''))
    print env['PATH']
    env['LDFLAGS'] = '-Wl,--allow-shlib-undefined -L%s --sysroot %s/platforms/android-22/arch-%s' % (build_dir, ndk_home, arch_name)
    env['CFLAGS'] = '-mandroid -Wno-attributes -fomit-frame-pointer --sysroot %s/platforms/android-22/arch-%s -DNO_MALLINFO -I%s/sysroot/usr/include -I%s/sysroot/usr/include/%s -I./openssl/openssl-1.0.2h/include/' % (
            ndk_home, arch_name, ndk_home, ndk_home, gcc_name)
    env['OPENSSL_VERSION'] = '1.0.2h'
    env['ac_cv_header_langinfo_h'] = 'no'
    env['CONFIG_SITE'] = './config.site'
    call(['mkdir', '-p', build_dir])
    call(['rm', '-r', 'libs/'])
    call(['mkdir', 'libs'])
    build_openssl(env, arch_name, gnu_arch_name, gcc_name, build_dir)
    call(['./configure',
        'LDFLAGS=%s' % env['LDFLAGS'],
        'CFLAGS=%s' % env['CFLAGS'],
        '--host=%s' % host_arch,
        '--build=%s' % gnu_arch_name,
        '--prefix=%s' % build_dir,
        '--enable-shared', '--enable-optimizations',
        '--disable-ipv6',
        '--disable-toolbox-glue',
        '--disable-framework'], env=env)
    call(['make', '-j5', 'install',
        'HOSTPYTHON=python',
        'INSTSONAME=libpython2.7.so',
        'CROSS_COMPILE_TARGET=yes'], env=env)
    call(['cp', '%s/lib/libpython2.7.so' % build_dir, './target/%s' % android_name])
    #call(['make', 'distclean'])

if __name__ == '__main__':
    for arch_name, gnu_arch_name, gcc_name, android_name in archs:
        build(arch_name, gnu_arch_name, gcc_name, android_name)
