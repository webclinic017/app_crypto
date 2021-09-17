from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('templates.html')

if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.run(host='0.0.0.0', port=8000, debug=True)
