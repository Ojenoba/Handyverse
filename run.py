import os
from app import create_app

print(os.getcwd())
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)