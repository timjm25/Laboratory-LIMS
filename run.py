from lims.app import create_app

if __name__ == "__main__":
    create_app("lims.db").run(host="127.0.0.1", port=5109, debug=False)
