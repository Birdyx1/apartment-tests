pipeline {
    agent any

    stages {
        stage('检查 Python') {
            steps {
                sh 'python3 --version'
            }
        }

        stage('创建虚拟环境并安装依赖') {
            steps {
                sh 'python3 -m venv .venv'
                sh '.venv/bin/python -m pip install -r requirements.txt'
            }
        }

        stage('运行单条接口测试') {
            steps {
                sh 'APARTMENT_BASE_URL=http://host.docker.internal:8080 .venv/bin/python -m pytest -q tests/test_apartment.py::test_apartment_list'
            }
        }
    }
}