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

        stage('准备 Node.js 24') {
            steps {
                sh '''
                    set -eu
                    node_version=24.16.0
                    case "$(uname -m)" in
                        x86_64) node_arch=x64 ;;
                        aarch64|arm64) node_arch=arm64 ;;
                        *) echo "Unsupported Jenkins architecture: $(uname -m)" >&2; exit 1 ;;
                    esac
                    cache_dir="$JENKINS_HOME/.cache"
                    node_dir="$cache_dir/node-v${node_version}-linux-${node_arch}"
                    mkdir -p "$cache_dir"
                    if [ ! -x "$node_dir/bin/node" ]; then
                        archive="/tmp/node-v${node_version}-linux-${node_arch}.tar.xz"
                        curl -fsSL "https://nodejs.org/dist/v${node_version}/node-v${node_version}-linux-${node_arch}.tar.xz" -o "$archive"
                        tar -xJf "$archive" -C "$cache_dir"
                        rm -f "$archive"
                    fi
                    ln -sfn "$node_dir" "$cache_dir/node-24"
                    export PATH="$cache_dir/node-24/bin:$PATH"
                    node --version
                    npm --version
                '''
            }
        }

        stage('安装 Playwright 与 Chromium') {
            steps {
                sh '''
                    set -eu
                    export PATH="$JENKINS_HOME/.cache/node-24/bin:$PATH"
                    export PLAYWRIGHT_BROWSERS_PATH="$JENKINS_HOME/.cache/ms-playwright"
                    cd ui-tests
                    npm ci
                    npx playwright install chromium
                '''
            }
        }

        stage('运行全量接口回归') {
            steps {
                script {
                    def result = sh(
                        script: 'APARTMENT_BASE_URL=http://host.docker.internal:8080 APARTMENT_MINIO_ENDPOINT=host.docker.internal:9000 APARTMENT_MINIO_PUBLIC_ORIGIN=http://host.docker.internal:9000 .venv/bin/python -m pytest -q --alluredir=allure-results --clean-alluredir',
                        returnStatus: true
                    )
                    if (result != 0) {
                        currentBuild.result = 'FAILURE'
                    }
                }
            }
        }

        stage('运行全量 UI 回归') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'apartment-admin-login',
                        usernameVariable: 'PW_ADMIN_USERNAME',
                        passwordVariable: 'PW_ADMIN_PASSWORD'
                    ),
                    string(credentialsId: 'apartment-demo-captcha', variable: 'PW_DEMO_CAPTCHA')
                ]) {
                    script {
                        def result = sh(
                            script: '''
                                set -eu
                                export PATH="$JENKINS_HOME/.cache/node-24/bin:$PATH"
                                export PLAYWRIGHT_BROWSERS_PATH="$JENKINS_HOME/.cache/ms-playwright"
                                cd ui-tests
                                export CI=true
                                BASE_URL=http://host.docker.internal:3000 \
                                PW_STORAGE_STATE=tests/.auth/jenkins-admin.json \
                                npx playwright test
                            ''',
                            returnStatus: true
                        )
                        if (result != 0) {
                            currentBuild.result = 'FAILURE'
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            allure(
                allureVersion: 'allure3',
                results: [[path: 'allure-results']]
            )
            archiveArtifacts artifacts: 'allure-results/**, ui-tests/playwright-report/**, ui-tests/test-results/**', allowEmptyArchive: true
            sh 'rm -f ui-tests/tests/.auth/jenkins-admin.json'
        }
    }
}
