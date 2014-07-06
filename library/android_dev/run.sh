# Example for running
docker run -t -i -e DEBIAN_FRONTEND:noninteractive -e ANDROID_HOME:/usr/local/android-sdk -e PATH:$PATH:$ANDROID_HOME/tools -e PATH:$PATH:$ANDROID_HOME/platform-tools -e ANT_HOME:/usr/local/apache-ant -e PATH:$PATH:$ANT_HOME/bin -e JAVA_HOME:/usr/lib/jvm/java-6-oracle android_dev  
