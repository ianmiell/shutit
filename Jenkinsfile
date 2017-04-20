#!groovy

def nodename='cage'
def builddir='shutit-' + env.BUILD_NUMBER

try {
	stage('setupenv') {
		node(nodename) {
			sh 'mkdir -p ' + builddir
			dir(builddir) {
				checkout([$class: 'GitSCM', branches: [[name: '*/master']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: false, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[url: 'https://github.com/ianmiell/shutit']]])
			}
		}
	}
	
	stage('shutit_tests') {
		node(nodename) {
			dir(builddir + '/shutit-test/test') {
				withEnv(["SHUTIT=" + builddir + "/shutit"]) {
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
