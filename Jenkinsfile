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

        stage('运行全量接口回归') {
            steps {
                sh 'APARTMENT_BASE_URL=http://host.docker.internal:8080 APARTMENT_MINIO_ENDPOINT=host.docker.internal:9000 .venv/bin/python -m pytest -q --alluredir=allure-results --clean-alluredir'
            }
        }
    }

    post {
        always {
            allure(
                allureVersion: 'allure3',
                results: [[path: 'allure-results']]
            )
            archiveArtifacts artifacts: 'allure-results/**', allowEmptyArchive: true
        }
    }
}
