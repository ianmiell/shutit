#!/bin/bash
#http://patorjk.com/software/taag
DATA[0]="  SSSSS  hhh                t     I    t    ";
DATA[1]="SSSSSS   h:h               t:t   I:I  t:t   ";
DATA[3]=" SSS     h:h     uuu  uuu t:::t      t:::t  ";
DATA[4]="  SSS    h::hh   u:u  u:u  t:t   III  t:t   ";
DATA[5]="   SSSS  h:h hh  u:u  u:u  t:t   I:I  t:t   ";
DATA[6]="    SSSS h:h h:h u::uu::u  t:tt  I:I  t:tt ";
DATA[7]=" SSSSSS  h:h h:h  u::::u:u  t::t I:I   t::t";
DATA[8]="SSSSS    hhh hhh   uuuu uu   ttt III    ttt ";
REALoOFFSEToX=0 ;
REALoOFFSEToY=0;
drawochar() { VoCOORDoX=$1;
VoCOORDoY=$2;
tput cup $((REALoOFFSEToY + VoCOORDoY)) $((REALoOFFSEToX + VoCOORDoX));
printf %c ${DATA[VoCOORDoY]:VoCOORDoX:1};
};
trap 'exit 1' INT TERM;
trap 'tput setaf 9;
tput cvvis;
clear' EXIT;
tput civis;
clear;
for ((b=0; b<1; b++));
 do for ((c=1; c <= 1; c++));
  do tput setaf $c;
  for ((x=0; x<${#DATA[0]}; x++));
   do for ((y=0; y<=15; y++));
    do drawochar $x $y;
   done;
  done;
 done;
done;
sleep 2

                                                                                               
#DATA[0]="   SSSSSSSSSSSSS hhhhh                          ttt      IIIIIII    ttt     "; DATA[1]=" SS:::::::::::::Sh:::h                        tt::t      I:::::I  tt::t     "; DATA[2]="S::::SSSSSS:::::Sh:::h                        t:::t      I:::::I  t:::t     "; DATA[3]="S::::S     SSSSSSh:::h                        t:::t      II:::II  t:::t     "; DATA[4]="S::::S           h::h hhhh     uuuu   uuuutttt:::ttttt    I::Itttt:::ttttt  "; DATA[5]="S::::S           h::hh::::hh   u::u   u::ut::::::::::t    I::I:::::::::::t  "; DATA[6]=" S:::SSSS        h::::::::::h  u::u   u::ut::::::::::t    I::I:::::::::::t  "; DATA[7]="  SS:::::SSSSS   h:::::hh::::h u::u   u::uttt:::::tttt    I::Ittt:::::tttt  "; DATA[8]="    SS::::::::S  h::::h  h::::hu::u   u::u   t:::t        I::I   t:::t      "; DATA[9]="      SSSSSS:::S h:::h    h:::hu::u   u::u   t:::t        I::I   t:::t      "; DATA[10]="           S::::Sh:::h    h:::hu::u   u::u   t:::t        I::I   t:::t      "; DATA[11]="           S::::Sh:::h    h:::hu:::uuu:::u   t:::t  tttt  I::I   t:::t  tttt"; DATA[12]="SSSSSS     S::::Sh:::h    h:::hu::::::::::uu t::::tt:::tII::::I  t::::tt:::t"; DATA[13]="S:::::SSSSSS::::Sh:::h    h:::h u::::::::::u tt::::::::tI:::::I  tt::::::::t"; DATA[14]="S:::::::::::::SS h:::h    h:::h  :::::::u::u   t::::::ttI:::::I    t::::::tt"; DATA[15]=" SSSSSSSSSSSSS   hhhhh    hhhhh  uuuuuuu uuu    tttttt  IIIIIII     tttttt  "; REALoOFFSEToX=0 ;REALoOFFSEToY=0; drawochar() { VoCOORDoX=$1; VoCOORDoY=$2; tput cup $((REALoOFFSEToY + VoCOORDoY)) $((REALoOFFSEToX + VoCOORDoX)); printf %c ${DATA[VoCOORDoY]:VoCOORDoX:1}; }; trap 'exit 1' INT TERM; trap 'tput setaf 9; tput cvvis; clear' EXIT; tput civis; clear; for ((b=0; b<1; b++)); do for ((c=1; c <= 1; c++)); do tput setaf $c; for ((x=0; x<${#DATA[0]}; x++)); do for ((y=0; y<=15; y++)); do drawochar $x $y; done; done; done; done;

