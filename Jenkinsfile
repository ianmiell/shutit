#!groovy

def nodename='cage'
def builddir='shutit-' + env.BUILD_NUMBER
def branch=env.BRANCH_NAME

//nodename='welles'
//def nodetest() {
//  sh('echo alive on $(hostname)')
//}
//// By default we use the 'welles' node, which could be offline.
//try {
//  // Give it 5 seconds to run the nodetest function
//  timeout(time: 5, unit: 'SECONDS') {
//    node(nodename) {
//      nodetest()
//    }
//  }
//} catch(err) {
//  // Uh-oh. welles not available, so use 'cage'.
//  nodename='cage'
//}

try {
	lock('shutit_tests') {	
		stage('setupenv') {
			node(nodename) {
				sh 'mkdir -p ' + builddir
				dir(builddir) {
					checkout([$class: 'GitSCM', branches: [[name: '*/' + branch]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: false, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[url: 'https://github.com/ianmiell/shutit']]])
				}
			}
		}
		stage('shutit_tests') {
			node(nodename) {
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


