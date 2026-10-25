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

        stage('收集测试用例') {
            steps {
                sh '.venv/bin/python -m pytest --collect-only -q'
            }
        }
    }
}