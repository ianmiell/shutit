#!groovy

def nodename='cage'
def builddir='shutit-' + env.BUILD_NUMBER

try {
	stage('setupenv') {
		node(nodename) {
			sh 'mkdir -p ' + builddir
			dir(builddir) {
				checkout scm
			}
		}
	}
	
	stage('shutit_tests') {
		node(nodename) {
			dir(builddir + '/test') {
				withEnv(["SHUTIT=/usr/local/bin/shutit"]) {
					sh './run.sh'
				}
				
			}
		}
	}
	mail bcc: '', body: '''See: http://jenkins.meirionconsulting.tk/job/shutit''', cc: '', from: 'shutit-jenkins@jenkins.meirionconsulting.tk', replyTo: '', subject: 'Build OK', to: 'ian.miell@gmail.com'
} catch(err) {
	mail bcc: '', body: '''See: http://jenkins.meirionconsulting.tk/job/shutit

''' + err, cc: '', from: 'shutit-jenkins@jenkins.meirionconsulting.tk', replyTo: '', subject: 'Build failure', to: 'ian.miell@gmail.com'
	throw(err)
}
