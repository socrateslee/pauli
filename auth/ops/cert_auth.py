# coding:utf-8
import os
import re
import time
import uuid
import random
import sys
import getopt
import logging
from ... import conf
from ..models import User, CertLogin

logger = logging.getLogger(__name__)


def get_user(**headers):
    if headers.get('Ssl-Client-Verified') != 'SUCCESS':
        return None
    if not headers.get('Ssl-Client-S-Dn'):
        return None
    serial = headers.get('Ssl-Client-Serial')
    if not serial:
        return None
    else:
        serial = str(int(serial, 16))
    cert_login = CertLogin.objects(serial=serial, soft_del=False).first()
    if not cert_login:
        return None
    user = User.objects(id=cert_login.user_id, soft_del=False).first()
    return user


def revoke(user_id=None, serial=None):
    cert_login_list
    if user_id:
        cert_login_list = list(CertLogin.objects(user_id=user_id, soft_del=False))
    elif serial:
        cert_login_list = list(CertLogin.objects(serial=serial, soft_del=False))
    for cert_login in cert_login_list:
        cert_login.soft_del = True
        cert_login.info['revoke_timestamp'] = int(time.time())
        cert_login.save()
        return True
    return False


def generate_cert(user, ca_key_path, ca_cert_path, csr_path='', key_path=''):
    user = user if hasattr(user, 'id')\
           else User.objects(id=user).first()
    if not user:
        return False, '用户不存在'
    serial = str(int(time.time() * 1000)) + str(random.randint(0, 10000))
    if CertLogin.objects(serial=serial).first():
        return False, '证书Serial已经存在'
    if key_path:
        if not key_path.endswith('.key'):
            return False, 'key文件必须以.key结尾'
        dirname = os.path.dirname(key_path)
        basename = os.path.basename(key_path)
        csr_name = basename.replace('.key', '.csr')
        csr_path = '%s/%s' % (dirname, csr_name) if dirname else csr_name
        csr_cmd = 'openssl req -new -key %s -out %s -subj '\
                  + '"/C=CN/ST=Beijing/L=Beijing/O=Gsitanfu Ltd./OU=/CN=gstianfu.com/serialNumber=%s"'
        print(csr_cmd % (key_path, csr_path, serial))
        ret = os.system(csr_cmd % (key_path, csr_path, serial))
        if ret != 0:
            return False, 'csr生成失败'
    if csr_path:
        if not csr_path.endswith('.csr'):
            return False, 'csr文件必须以.csr结尾'
        dirname = os.path.dirname(csr_path)
        basename = os.path.basename(csr_path)
        crt_name = basename.replace('.csr', '.crt')
        crt_path = "%s/%s" % (dirname, crt_name) if dirname else crt_name
        crt_cmd = 'openssl x509 -req -days 1000 -in %s -CA %s -CAkey %s -set_serial %s -out %s'
        ret = os.system(crt_cmd % (csr_path, ca_cert_path, ca_key_path, serial, crt_path))
        if ret != 0:
            return False, 'crt文件生成失败'
        print("Serial: %s" % serial)
        print("Certificate:")
        os.system("cat %s" % crt_path)
    cert_login = CertLogin(user_id=str(user.id), serial=serial)
    cert_login.save()
    return True, cert_login.serial


def generate_cert_user(name, ca_key_path, ca_cert_path, csr_path='', key_path=''):
    name = name.strip()
    if not name:
        return False, "用户名字不能为空"
    user = User(name=name)
    user.save()
    succ, msg = generate_cert(user, ca_key_path, ca_cert_path,
                              csr_path=csr_path, key_path=key_path)
    if not succ:
        user.delete()
        return succ, msg
    else:
        ret = {'serial': msg,
               'user_id': str(user.id)}
        return succ, ret


def help():
    docstr = '''
Generate user and cert:
    python -m auth.ops.cert_auth genuser <NAME OF USER> <CA_KEY_PATH> <CA_CERTT_PATH> --key_path <KEY_PATH>
    python -m auth.ops.cert_auth genuser <NAME OF USER> <CA_KEY_PATH> <CA_CERTT_PATH> --csr_path <CSR_PATH>

Generate cert:
    python -m auth.ops.cert_auth gencert <CA_KEY_PATH> <CA_CERTT_PATH> --user_id <USER_ID> --key_path <KEY_PATH>
    python -m auth.ops.cert_auth gencert <CA_KEY_PATH> <CA_CERTT_PATH> --user_id <USER_ID> --csr_path <CSR_PATH>

Revoke cert:
    python -m auth.ops.cert_auth revoke --user_id <USER_ID>
    python -m auth.ops.cert_auth revoke --serial <SERIAL>
'''
    print(docstr)


def main():
    opts, args = getopt.gnu_getopt(sys.argv[1:], "",
                                   ["help", "user_id=", "serial=",
                                    "csr_path=", "key_path="])
    opts = dict(opts)
    if '--help' in opts:
        help()
        return
    if args[0] == 'revoke':
        print(revoke(user_id=opts.get('--user_id'),
                     serial=opts.get('--serial')))
    elif args[0] == 'gencert':
        ca_key_path = args[1]
        ca_cert_path = args[2]
        user_id = opts.get('--user_id')
        print(generate_cert(user_id, ca_key_path, ca_cert_path,
                            csr_path=opts.get('--csr_path'),
                            key_path=opts.get('--key_path')))
    elif args[0] == 'genuser':
        name = args[1]
        ca_key_path = args[2]
        ca_cert_path = args[3]
        print(generate_cert_user(name, ca_key_path, ca_cert_path,
                                 csr_path=opts.get('--csr_path'),
                                 key_path=opts.get('--key_path')))
    else:
        help()

if __name__ == '__main__':
    main()
