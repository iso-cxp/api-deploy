from flask import Flask, jsonify, render_template, make_response
from flask import request, Response, redirect
from functools import update_wrapper, wraps
import traceback
import deployer

app = Flask(__name__)

config={
    'staging_path': '/var/www/XE-API-staging',
    'production_path': '/var/www/XE-API-prod',
    'key_filename':'keys/id_rsa',
    'username':'vagrant'
}

api_servers={
    0: '192.168.50.4',
    1: 'vagrant',
    2: 'local.cxpxe.net'
}

testing_server={
    'host': 'vagrant',
    'username': 'vagrant',
    'key_filenmame': 'keys/id_rsa',
    'tests_path': '/var/www/XE-API/test'
}


# shitty auth BEGIN
def valid_login(username, password):
    return username == 'deploy' and password == 'shipit!'

def check_token(token):
    return token == 'legit' # str safe comparison

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # return f(*args, **kwargs)
        # auth = request.authorization
        token = request.cookies.get('token')
        if not token or not check_token(token):
            return Response('Access denied', 403)
        return f(*args, **kwargs)
    return decorated
# SHITTY AUTH END

# Decorators shmecorators
def crossdomain():
    def decorator(f):
        def wrapped_function(*args, **kwargs):
            resp = make_response(f(*args, **kwargs))

            h = resp.headers
            h['Access-Control-Allow-Origin'] = request.headers.get('Origin') or '*'
            h['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
            h['Access-Control-Allow-Credentials'] = 'true'
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


@app.route('/login', methods=['GET', 'POST'])
@crossdomain()
def login():
    error = None
    if request.method == 'POST':
        if valid_login(request.form['username'], request.form['password']):
            resp = make_response('Redirect', 302)
            resp.set_cookie('token', 'legit')
            resp.headers['Location'] = request.args.get('return_url')
            return resp
            # return redirect(request.args.get('return_url'), code=302)
        else:
            error = 'Invalid username/password'

    return render_template('login.html', error=error)

    if request.method == 'POST':
        check_auth()
    else:
        return render_template('login.html')
    # print(request.headers.Referer)
    if (check_auth()):
        pass
    if len(request.headers['Referer']):
        return redirect(request.headers['Referer'], code=302)
    else:
        return jsonify(result='Login success. No referer', success=False)


# Run tests
@app.route('/test/<string:environment>')
@crossdomain()
@requires_auth
def test(environment):
    client = None
    try:
        if environment in ['staging', 'production']:
            client = deployer.connect(testing_server['host'], config)
            success, results = deployer.test(client, environment, testing_server)
            return jsonify(result=results, success=success)
        else:
            return jsonify(result='Invalid environment', success=False)
    except Exception as error:
        traceback.print_exc()
        return jsonify(result=traceback.format_exception_only(type(error), error)[0], success=False)
    finally:
        if client:
            client.close()


# Execute git pull for staging repository
@app.route('/update/<int:server_id>')
@crossdomain()
@requires_auth
def update(server_id):
    client = None
    try:
        if server_id in api_servers:
            client = deployer.connect(api_servers[server_id], config)
            result = deployer.update(client, config['staging_path'])
            print(result)
            if len(result['err']):
                return jsonify(result=result, success=False)
            else:
                return jsonify(result=result, success=True)
        else:
            return jsonify(result='Server not found', success=False)
    except Exception as error:
        traceback.print_exc()
        return jsonify(result=traceback.format_exception_only(type(error), error)[0], success=False)
    finally:
        if client:
            client.close()



# Gather git info from prod/staging repos
@app.route('/getinfo/<int:server_id>')
@crossdomain()
@requires_auth
def getinfo(server_id):
    client = None
    try:
        if server_id in api_servers:
            client = deployer.connect(api_servers[server_id], config)
            result = deployer.getinfo(client, api_servers[server_id], config['staging_path'], config['production_path'])
            return jsonify(result=result, success=len(result['staging']['errors']) == 0 and len(result['production']['errors']) == 0)
        else:
            return jsonify(result='Server not found', success=False)
    except Exception as error:
        traceback.print_exc()
        return jsonify(result=traceback.format_exception_only(type(error), error)[0], success=False)
    finally:
        if client:
            client.close()


# Swap staging-production symlinks
@app.route('/swap/<int:server_id>')
@crossdomain()
@requires_auth
def swap(server_id):
    client = None
    try:
        if server_id in api_servers:
            client = deployer.connect(api_servers[server_id], config)
            result = deployer.swap(client, config['staging_path'], config['production_path'])
            if len(result['stderr']) == 0:
                return jsonify(result=result, success=True)
            else:
                return jsonify(result=result, success=False)
        else:
            return jsonify(result='Server not found', success=False)
    except Exception as error:
        traceback.print_exc()
        return jsonify(result=traceback.format_exception_only(type(error), error)[0], success=False)
    finally:
        if client:
            client.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)
