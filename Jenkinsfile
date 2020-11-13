pipeline {
    agent any
    environment {
        IMAGE_NAME = 'eu.gcr.io/talgreining-is/tiro-tts'
        REGISTRY_CREDENTIAL = 'talgreining-is'
        buildImage = ''
        testImage = ''
        runtimeImage = ''
    }
    stages {
        stage('Build') {
            steps {
                script {
                    buildImage = docker.build("${IMAGE_NAME}:git${GIT_COMMIT[0..7]}",
                                              "--target=build .")
                }
            }
        }
        // stage('Test') {
        //     steps {
        //         script {
        //             testImage = docker.build("${IMAGE_NAME}:git${GIT_COMMIT[0..7]}",
        //                                      "--target=test .")
        //             testImage.inside {
        //                 sh 'cp -r /src/junit.xml junit.xml'
        //             }
        //             junit 'junit.xml'
        //         }
        //     }
        // }
        stage('Build & push runtime container image') {
            steps {
                script {
                    runtimeImage = docker.build("${IMAGE_NAME}:git${GIT_COMMIT[0..7]}",
                                                "--target=runtime-prod .")
                    docker.withRegistry('https://eu.gcr.io', 'gcr:talgreining-is') {
                        runtimeImage.push(
                            "git${GIT_COMMIT[0..7]}-build${BUILD_NUMBER}")
                        runtimeImage.push("git${GIT_COMMIT[0..7]}")
                        runtimeImage.push("latest")
                    }
                }
            }
        }
        stage('Deploy - Staging') {
            when {
                branch 'master'
            }
            steps {
                echo 'Deploying to k8s staging environment'
		echo 'NOT DOING ANYTHING!!'
            }
            post {
                 always {
                    jiraSendDeploymentInfo(
                        site: 'tiro-is.atlassian.net',
                        environmentId: 'staging',
                        environmentName: 'staging',
                        environmentType: 'staging'
                    )
                }
            }
        }
        // stage('Sanity check') {
        //     when {
        //         branch 'master'
        //     }
        //     steps {
        //         input('Does the staging environment look fine? ' +
        //               'Should we deploy to production?')
        //     }
        // }
        stage('Deploy - Production') {
            when {
                branch 'master'
            }
            steps {
                echo 'Deploying to k8s production environment'
		withKubeConfig([credentialsId: 'gke-kubeconfig']) {
		    sh "kubectl kustomize k8s/overlays/prod | sed 's/%GIT_COMMIT%/git${GIT_COMMIT[0..7]}/'  | kubectl apply -f -"
		    echo 'Waiting for successful rollout...'
		    sh 'kubectl rollout status -w deploy/tiro-main-website-deployment'
		}
            }
            post {
                 always {
                    jiraSendDeploymentInfo(
                        site: 'tiro-is.atlassian.net',
                        environmentId: 'production',
                        environmentName: 'production',
                        environmentType: 'production'
                    )
                }
            }
        }
    }
    post {
        always {
                sh "docker image ls"
                jiraSendBuildInfo site: 'tiro-is.atlassian.net'
            }
    }
}
