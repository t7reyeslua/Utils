#include <windows.h>
#include <stdio.h>
#include <strings.h>
// Declaraciones ----------------------------------

COMMTIMEOUTS touts;
HANDLE serial;
char nombrePuerto[10];
int totalChars, totalSnd, totalRcv, bps;
unsigned char caracter; //char que se lee o recibe
unsigned char bufferRx;
int i;
unsigned char Fila[6];
 //-----------------------------------------------
  //*************************************************************************************
//Prototipos de funciones

HANDLE abre_y_configura_serial(char *nombrePuerto, int velocidad, COMMTIMEOUTS touts);
int envia_serial(HANDLE serial, unsigned char *buffer, int cantidad_a_enviar);
int recibe_serial(HANDLE serial, unsigned char *buffer, int cantidad_a_recibir);
int cierra_serial(HANDLE serial);

//*************************************************************************************

//*************************************************************************************
//Rutinas genéricas y de utilería del programa


HANDLE abre_y_configura_serial(char *nombrePuerto, int velocidad, COMMTIMEOUTS touts){
	DCB dcb;
	HANDLE handle;

	touts.ReadTotalTimeoutConstant = 100;
	touts.WriteTotalTimeoutConstant = 100;

	handle = CreateFile((const char *)nombrePuerto,GENERIC_WRITE | GENERIC_READ,0,NULL,OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL,NULL);
	//sin paridad, 8 bits de datos y un bit de stop.
	if (handle == NULL){
		printf("Error al abrir el HANDLE");
	}else{

	dcb.BaudRate= CBR_4800;
	dcb.ByteSize = 8;
	dcb.StopBits = ONESTOPBIT;
	dcb.Parity = NOPARITY;
	
	GetCommState(handle,&dcb);
	SetCommTimeouts(handle,&touts);
	SetCommState(handle,&dcb);
	}
	return handle;
}

int envia_serial(HANDLE serial, unsigned char *bufferTx, int cantidad_a_enviar){
	int state;
	int totalWritten;
	
	state=WriteFile(serial,(char *)bufferTx,(DWORD) cantidad_a_enviar, (PDWORD) &totalWritten,NULL);
	
	return totalWritten;
}

int recibe_serial(HANDLE serial, unsigned char *buffer, int cantidad_a_recibir){
	int state;
	int totalRead;

	state=ReadFile(serial,(char *)buffer,(DWORD) cantidad_a_recibir, (PDWORD) &totalRead,NULL);
	
	return totalRead;
}

int cierra_serial(HANDLE serial){
	int state = CloseHandle(serial);		//Cierra el "handle"
	return state;
}

 int main()
{
    unsigned char quest = 1;
    sprintf(nombrePuerto,"COM8");
    bps = 4800;
    serial = abre_y_configura_serial(nombrePuerto,bps,touts);
    
    while (quest){
    printf("Esperando datos a recibir por SERIAL... \n");
    
    for(i=0; i<7; i++) {
           totalRcv = 0;
           while (totalRcv == 0){
                 totalRcv = recibe_serial(serial, &bufferRx, 1);
           }
           Fila[0]=Fila[1];
	         Fila[1]=Fila[2];
           Fila[2]=Fila[3];
      	   Fila[3]=Fila[4];
   	       Fila[4]=Fila[5];
		       Fila[5]=Fila[6];
		       Fila[6]=bufferRx;
           printf("Dato Recibido[%d]= %X \n", i,bufferRx);
    }
    //printf ("Cantidad de datos recibidos: %d \n", totalRcv);
    
    for (i=3; i<6; i++){
        Fila[i] = Fila[i]+1;    
    }
    
    for (i=0; i<7; i++){
        totalSnd=envia_serial(serial, &Fila[i],1); 
        Sleep(20);
        printf("Enviando campo[%d]= %X... \n",i,Fila[i]);
    }//for 
    
    printf(" \nPresione [0] para salir u cualquiera para repetir: ");
    scanf( "%d", &quest);
   // int totalRcv = 0;
    //while (totalRcv == 0){
    //      totalRcv = recibe_serial(serial, &quest, 1);
    //}
    printf("\n");
    
    }
    cierra_serial(serial);
     
    return 0;
}
 
 
