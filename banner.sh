#!/bin/bash
#http://patorjk.com/software/taag
DATA[0]="  SSSS hh           tt  III  tt ";
DATA[1]=" SSS   hh    uu uu tttt III tttt";
DATA[2]="   SSS hhhh  uu uu  tt   I   tt";
DATA[3]="  SSS  hh hh uuuuu  tt  III  tt";
DATA[4]="SSSS   hh hh  uu uu  tt III   tt";
REALoOFFSEToX=0; REALoOFFSEToY=0;
drawochar() { VoCOORDoX=$1; VoCOORDoY=$2; tput cup $((REALoOFFSEToY + VoCOORDoY)) $((REALoOFFSEToX + VoCOORDoX)); printf %c ${DATA[VoCOORDoY]:VoCOORDoX:1}; };
trap 'exit 1' INT TERM; trap 'tput setaf 9; tput cvvis; clear' EXIT; tput civis; clear;
for ((b=0; b<5; b++));
 do for c in 0 1 2 3 4 5 0;
  do tput setaf $c;
  for ((x=0; x<${#DATA[0]}; x++));
   do for ((y=0; y<=4; y++));
    do drawochar $x $y;
   done;
  done;
 done;
done

#		self.send_file('/tmp/asd','''#!/bin/bash
#DATA[0]="  SSSS hh           tt  III  tt ";
#DATA[1]=" SSS   hh    uu uu tttt III tttt";
#DATA[2]="   SSS hhhh  uu uu  tt   I   tt";
#DATA[3]="  SSS  hh hh uuuuu  tt  III  tt";
#DATA[4]="SSSS   hh hh  uu uu  tt III   tt";
#REALoOFFSEToX=0; REALoOFFSEToY=0;
#drawochar() { VoCOORDoX=$1; VoCOORDoY=$2; tput cup $((REALoOFFSEToY + VoCOORDoY)) $((REALoOFFSEToX + VoCOORDoX)); printf %c ${DATA[VoCOORDoY]:VoCOORDoX:1}; };
#trap 'exit 1' INT TERM; trap 'tput setaf 9; tput cvvis; clear' EXIT; tput civis; clear;
#for ((b=0; b<5; b++));
# do for c in 0 1 2 3 4 5 0;
#  do tput setaf $c;
#  for ((x=0; x<${#DATA[0]}; x++));
#   do for ((y=0; y<=4; y++));
#    do drawochar $x $y;
#   done;
#  done;
# done;
#done''')
#		self.send('chmod +x /tmp/asd')
#		self.send('/tmp/asd',echo=True)
#		self.send('rm -f /tmp/asd',echo=True)
