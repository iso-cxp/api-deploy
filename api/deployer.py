import paramiko
from time import gmtime, strftime

colors = {
    'reset': '\033[0m',
    'red': '\033[0;31m',
    'blue': '\033[0;34m',
    'yellow': '\033[0;33m',
    'green': '\033[0;32m',
    'magenta': '\033[0;35m',
}

log_filename='/var/log/terminal/terminal.log'
# log_filename='../tmp/terminal.log' # REMOVE

# print and log
def output(s, color='reset', need_to_log=True):
    if need_to_log:
        print(colors[color] + s + colors['reset'])
        log(s, color)


# white to a log file
def log(s, color):
    log_file = open(log_filename, 'a')
    log_file.write('<div>[' + strftime("%c", gmtime()) + '] <span class="c_%s">%s</span></div>\n' % (color, s))
    log_file.close()


# Connect to server via ssh
def connect(host, config):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    output('Connecting to ' + host + '...')
    client.connect(host, username=config['username'], key_filename=config['key_filename'])
    return client


# get repo status (commit, time, etc.)
def get_status(client, path):

    # @TODO aggregate errros
    errors, commit_hash = exec_remote("git log -n 1 --pretty=format:'%H'", client, path)
    errors, commit_time = exec_remote("git log -n 1 --pretty=format:'%ar'", client, path)
    errors, commit_time_unix = exec_remote("git log -n 1 --pretty=format:'%at'", client, path)
    errors, commit_message = exec_remote("git log -n 1 --pretty=format:'%s'", client, path)

    return {
        "commit_hash": commit_hash[0] if len(commit_hash) else '',
        "commit_time": commit_time[0] if len(commit_time) else '',
        "commit_time_unix": commit_time_unix[0] if len(commit_time_unix) else '',
        "commit_message": commit_message[0] if len(commit_message) else '',
        "errors": errors
    }

# Execute git pull
def update(client, staging_path):
    data={}
    data['err'], data['out'] = exec_remote('date', client, staging_path)

    return data


# Gather git info from staging and production repositories
def getinfo(client, host, staging_path, production_path):

    return {
        "staging": get_status(client, staging_path),
        "production": get_status(client, production_path),
        "ip": host
    }

def test(client, environment, testing_server):
    print('deployer.test invoked')

    # Run test
    # stderr, stdout = exec_remote('php codecept.phar run api AdpemployeeCest --silent --report --env %s && echo SUCCESS' % environment, client, testing_server['tests_path'])
    stderr, stdout = exec_remote('(php codecept.phar run --silent --report --env %s && echo SUCCESS) | aha --no-header -b ' % environment, client, testing_server['tests_path'])
    return stdout[len(stdout)-1] == 'SUCCESS' if len(stdout) > 0 else False, {"stderr": stderr, "stdout": stdout}


# Execute command on remote server
def exec_remote(cmd, client, path='.', server='',log=True):
    cmd = "cd %s && %s" % (path, cmd)
    output('Executing: "' + cmd + '" on ' + server)
    stdin, stdout, stderr = client.exec_command(cmd)
    return handle_result(stderr, stdout, log)


def swap(client, staging_path, production_path):

    commands=[
        'cp -d %s %s-tmp' % (production_path,production_path),
        'cp -d %s %s-tmp' % (staging_path,staging_path),
        'mv -T %s-tmp %s' % (staging_path,production_path),
        'mv -T %s-tmp %s' % (production_path,staging_path)
    ]

    stderr, stdout = exec_remote(' && '.join(commands), client)

    return {"stdout": stdout, "stderr": stderr}


def handle_result(stderr, stdout, log):
    err = stderr.read()
    err_lines = []
    if len(err):
        for line in err.decode('utf-8').split('\n'):
            if len(line):
                output(line, 'red', log)
                err_lines.append(line)

    out = stdout.read()
    out_lines = []
    if len(out):
        for line in out.decode('utf-8').split('\n'):
            if len(line):
                output(line, 'blue', log)
                out_lines.append(line)

    return err_lines, out_lines
