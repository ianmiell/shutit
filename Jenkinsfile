#!groovy

def builddir='shutit-' + env.BUILD_NUMBER
def branch=env.BRANCH_NAME

try {
	lock('shutit_tests') {	
		stage('setupenv') {
			node() {
				sh 'mkdir -p ' + builddir
				dir(builddir) {
					checkout([$class: 'GitSCM', branches: [[name: '*/' + branch]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: false, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[url: 'https://github.com/ianmiell/shutit']]])
				}
			}
		}
		stage('shutit_tests') {
			node() {
				dir(builddir + '/shutit-test') {
					sh('PATH=$(pwd)/..:${PATH} ./run.sh -s tk.shutit.shutit_test shutit_branch ' + branch + ' -l info 2>&1')
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


