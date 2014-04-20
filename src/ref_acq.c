#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <signal.h>
#include <unistd.h>
#include <time.h>
#include "pcieSrTr_ioctl.h"
#define READ_BUFFER_SIZE 4096 
//0x1000//0x5000 //0x800//   size in ints (1024 * 16)
#define DMA_SAMPLE_PACKET_SIZE 0x1000  //(10000*20480) 
//0x186A0000//0x10000000

char *PROC_LOC = "/proc/pcieSrTr";
char DEVNAME[] = "/dev/pcie0";
void sigint_handler(int sig);

/* prototype */

void printProc(void) {
    int flags = O_RDWR;
    int cfd = open(PROC_LOC, flags);
    char readBuffer[READ_BUFFER_SIZE];
    if (cfd > 0) {
        memset(readBuffer, 0, READ_BUFFER_SIZE);
        read(cfd, readBuffer, READ_BUFFER_SIZE);
        fprintf(stdout, "%s", readBuffer);
        close(cfd);
    }
}

/************************************************************
 * Function: SRTR_ATCA_readparam()                          *
 * Purpose:  read parameters from file.                     *
 * Args:                                                    *
 *  - filename_par: parameters filename                     *
 *  - *param: pointer to parameter allocated buffer         *
 *  - nparams: number of parameters to load                 *
 * Return:                                                  *
 *  - *param: a) filled with nparams parameters             *
 *            b) NULL CASE FAILURE                          *
 *                                             PRC/01042009 *
 ************************************************************/
int* SRTR_ATCA_readparam(char filename_par[100], int *param, int nparams){
FILE *fdp = NULL;

    fdp = fopen(filename_par, "rb");
    if (fdp == NULL) {
        printf("failed to open file for reading!\n");
        param = NULL;
    } else {
        fread(param, sizeof(int), nparams, fdp);
        fclose(fdp);
    }
    return(param);
}

/************************************************************
 * Function: SRTR_ATCA_splitdata()                          *
 * Purpose:  Split data file in timestamps and pulsewidth.  *
 * Args:                                                    *
 *  - filename_dt: data file name                           *
 *  - nsamples: number of samples                           *
 *  - pulsewidth: value of the pulsewidth                   *
 * OutPut:																									*
 *  - ts_(filename_dt): timestamp file											*
 *  - pw_(filename_dt): pulsewidth file											*
 *                                             PRC/31032009 *
 ************************************************************/
void SRTR_ATCA_splitdata(char filename_dt[100], int nsamples, int pulsewidth){
char filename_ts[100] = "ts_";
char filename_pw[100] = "pw_";
unsigned int i,j,k,l;
unsigned int elem;

FILE *fdt = 0;
FILE *fts = 0;
FILE *fpw = 0;

short *pw;
unsigned short *dt;
unsigned long long *ts;

    // init vars
    strcat(filename_ts, filename_dt);
    strcat(filename_pw, filename_dt);

    fdt = fopen(filename_dt, "rb");
    if (fdt == NULL) {
        printf("failed to open data file for reading!\n");
    } else {

        // allocate resources
        dt = (unsigned short*) calloc(nsamples, sizeof (unsigned short));
        ts = (unsigned long long*) calloc(nsamples, sizeof (unsigned long long));
        pw = (short*) calloc(nsamples, sizeof (short));

        if ( (dt == NULL) || (ts == NULL) || (pw == NULL) ){
            printf("failed to allocate mem resources!\n");
            fclose(fdt);
        }else{

            elem = fread(dt, sizeof(short), nsamples, fdt);
            fclose(fdt);

            // split dt
            j = 0; k = 0; l = 0;
            for(i = 0; i<nsamples; i++){
                if(k == j*pulsewidth){
                    ts[l] = (dt[i+3]<<48)+(dt[i+2]<<32)+(dt[i+1]<<16)+dt[i];
                    j++; l++; i+=3;
                }else{
                    pw[k] = dt[i];
                    k++;
                }
            }

            fts = fopen(filename_ts, "wb");
            if (fts == NULL) {
                printf("failed to open ts file for writing!\n");
            } else {
                elem = fwrite(ts, sizeof(unsigned long long), l, fts);
                printf("TS Values (64bits):   %d\n", elem);
                fclose(fts);
            }
            fpw = fopen(filename_pw, "wb");
            if (fpw == NULL) {
                printf("failed to open pw file for writing!\n");
            } else {
                elem = fwrite(pw, sizeof(short), k, fpw);
                printf("PW Values (16bits):   %d\n", elem);
                fclose(fpw);
            }
            // free allocated resources
            free(dt);
            free(ts);
            free(pw);
        }
    }
}


int main(int argc, char** argv) {
    int K          = 0;
    int L          = 0;
    int M          = 0;
    int T          = 0;
    int DQTP       = 0;
    int COMPL      = 0;
    int PTRG       = 0; 
    int PWIDTH		 = 0;
    int Trg_Acc    = 0;
    int i          = 0;
    int pll        = 0;
    int fd         = 0;
    int ack        = 0;
    int softtrg    = 0;
    int flags      = O_RDWR;
    int nSamples   = 0x1000;
    int offset     = 0;
    int offsetJump = 0;


    unsigned int nBytes = 0;
    int channel = 1;
    unsigned int postTrigger = 420000; //periodo de 16 ns (base 
    //temporal passa a estar em segundos
    int waitTime = 0;

    char *outputFilename    = NULL;
    char *deviceName        = DEVNAME;
    // char *realFilename[64];
		char  realFilename[64];
    int   nOnChannels       = 0;
    int   currentChannel    = 0;
    int   currentRead       = 0;
    int   nbytesClusterSize = 0;
    FILE *outputFD          = NULL;

    unsigned short buffer[READ_BUFFER_SIZE / sizeof (short) ];
    //unsigned short *data = NULL;
    int ret;

    time_t t0 = 0;
    time_t t1 = 0;
    
    char filename_dt[4][100];
    int nparams = 1024;
    int *param = NULL;
    FILE *fdp = NULL;
    int j = 0;
    int z = 0, cnter = 0;
    char *filename_par = NULL;

    /* iterate over all arguments */
    for (i = 1; i < argc; i++) {
        if (strcasecmp("K", argv[i]) == 0) {
            K = atoi(argv[++i]);
            continue;
        }
        if (strcasecmp("L", argv[i]) == 0) {
            L = atoi(argv[++i]);
            continue;
        }
        if (strcasecmp("M", argv[i]) == 0) {
            M = atoi(argv[++i]);
            continue;
        }
        if (strcasecmp("T", argv[i]) == 0) {
            T = atoi(argv[++i]);
            continue;
        }
        if (strcasecmp("pll", argv[i]) == 0) {
            pll = atoi(argv[++i]);
            continue;
        }
	  if (strcasecmp("COMPL", argv[i]) == 0) {
            COMPL = atoi(argv[++i]);
            continue;
    }
    if (strcasecmp("PTRG", argv[i]) == 0) {
            PTRG = atoi(argv[++i]);
            continue;
    }
    if (strcasecmp("PWIDTH", argv[i]) == 0) {
            PWIDTH = atoi(argv[++i]);
            continue;
    }    
    
    if (strcasecmp("Trg_Acc", argv[i]) == 0) {
            Trg_Acc = atoi(argv[++i]);
            continue;
    }  
            
        if (strcasecmp("dqtp", argv[i]) == 0) {
            DQTP = atoi(argv[++i]);
            continue;
        }
        if (strcasecmp("nsamples", argv[i]) == 0) {
            nSamples = atoi(argv[++i]);
            continue;
        }
        if (strcasecmp("time", argv[i]) == 0) {
            waitTime = atoi(argv[++i]);
            continue;
	}
        if (strcasecmp("channel", argv[i]) == 0) {
            channel = atoi(argv[++i]);
            continue;
        }
        if (strcasecmp("post", argv[i]) == 0) {
            postTrigger = atoi(argv[++i])*4200000;
            continue;
        }
        if (strcasecmp("file", argv[i]) == 0) {
            outputFilename = argv[++i];
            continue;
        }
        if (strcasecmp("devn", argv[i]) == 0) {
            deviceName = argv[++i];
            continue;
        }
        if (strcasecmp("ack", argv[i]) == 0) {
            ack = 1;
            continue;
        }
        if (strcasecmp("softtrg", argv[i]) == 0) {
            softtrg = 1;
            continue;
        }
        
        if (strcasecmp("infile", argv[i]) == 0) {
            filename_par = argv[++i];
            continue;
        }        
    }

    while (nSamples % 2048) {
        nSamples++;
    }

    printf("K=%d\n", K);
    printf("L=%d\n", L);
    printf("M=%d\n", M);
    printf("T=%d\n", T);
    printf("PLL=%d\n", pll);
    printf("COMPL=%d\n", COMPL);
    printf("PTRG=%d\n", PTRG);
    printf("PWIDTH=%d\n", PWIDTH);  
    printf("Trg_Acc=%d\n", Trg_Acc);  
    printf("CHANNEL=%d\n", channel);
    printf("Number of samples=%d\n", nSamples);
    printf("File Parameter=%s\n", filename_par);
    printf("Output file=%s\n", outputFilename);
    printf("Device Name=%s\n", deviceName);

    fd = open(deviceName, flags);
    if (fd < 1) {
        printf("Error opening device!\n");
        return -1;
    }

    printf("Device %s opened successfully\n", deviceName);

    printf("Configuring device\n");
    ret = ioctl(fd, PCIE_SRTR_IOCS_PLLCFG, &pll);
    if (ret == -1) {
        fprintf(stderr, "Error: cannot ioctl device %s \n", deviceName);
        return -1;
    }
    ret = ioctl(fd, PCIE_SRTR_IOCS_COMPL, &COMPL);
    if (ret == -1) {
        fprintf(stderr, "Error: cannot ioctl device %s \n", deviceName);
        return -1;
    }
    ret = ioctl(fd, PCIE_SRTR_IOCS_PTRG, &PTRG);
    if (ret == -1) {
        fprintf(stderr, "Error: cannot ioctl device %s \n", deviceName);
        return -1;
    }
    ret = ioctl(fd, PCIE_SRTR_IOCS_PWIDTH, &PWIDTH);
    if (ret == -1) {
        fprintf(stderr, "Error: cannot ioctl device %s \n", deviceName);
        return -1;
    }
    ret = ioctl(fd, PCIE_SRTR_IOCS_Trg_Acc, &Trg_Acc);
    if (ret == -1) {
        fprintf(stderr, "Error: cannot ioctl device %s \n", deviceName);
        return -1;
    }
    ret = ioctl(fd, PCIE_SRTR_IOCS_DQTP, &DQTP);
    if (ret == -1) {
        fprintf(stderr, "Error: cannot ioctl device %s \n", deviceName);
        return -1;
    }
    ret = ioctl(fd, PCIE_SRTR_IOCS_DATA_PROC_K, &K);
    if (ret == -1) {
        fprintf(stderr, "Error: cannot ioctl device %s \n", deviceName);
        return -1;
    }
    ret = ioctl(fd, PCIE_SRTR_IOCS_DATA_PROC_L, &L);
    if (ret == -1) {
        fprintf(stderr, "Error: cannot ioctl device %s \n", deviceName);
        return -1;
    }
    ret = ioctl(fd, PCIE_SRTR_IOCS_DATA_PROC_M, &M);
    if (ret == -1) {
        fprintf(stderr, "Error: cannot ioctl device %s \n", deviceName);
        return -1;
    }
    ret = ioctl(fd, PCIE_SRTR_IOCS_DATA_PROC_T, &T);
    if (ret == -1) {
        fprintf(stderr, "Error: cannot ioctl device %s \n", deviceName);
        return -1;
    }
    ret = ioctl(fd, PCIE_SRTR_IOCS_CHAN_ON_OFF, &channel);
    if (ret == -1) {
        fprintf(stderr, "Error: cannot ioctl device %s \n", deviceName);
        return -1;
    }

    // open param file
    if (filename_par != NULL) {
        fdp = fopen(filename_par, "rb");
        if (fdp == NULL) {
            printf("failed to open file for reading!\n");
        } else {
            // allocate mem resources
            param = (int*) calloc(nparams, sizeof (int));
            if(param == NULL){
                printf("failed to allocate mem resources!\n");
            }else{
                param = SRTR_ATCA_readparam(filename_par, param, nparams);
                for (j=0; j<nparams; j++) {
                    // send params to board
                    ret = ioctl(fd, PCIE_SRTR_IOCS_FILEDATA, &param[j]);
                    if (ret == -1) {
                        fprintf(stderr, "Error: cannot ioctl device %s \n", deviceName);
                        return -1;
                    }
                }
            }
            // free allocated resources
            free(param);
            fclose(fdp);
        }
    }   
    
    if (ack == 1) {
        if(channel & 0x1)
            nOnChannels++;
        if(channel & 0x2)
            nOnChannels++;      	
        if(channel & 0x4)
            nOnChannels++;
        if(channel & 0x8)
            nOnChannels++;

        if(outputFilename == NULL){
            printf("Output file name not specified. Using outX.bin as output\n");
            outputFilename = "out";
        }        

	nBytes = (nSamples * sizeof (short))*nOnChannels;
	ret = ioctl(fd, PCIE_SRTR_IOCS_ACQBYTESIZE, &nBytes);
        
        printf("Enabling acquisition\n");
        printf("The number of samples to acquire is %d\n", nSamples);
        printf("The number of bytes to acquire is %u\n", nBytes);
/*        printf("Hit any key to start acquisition\n");*/
/*        getchar();*/
        printf("Starting acquisition\n");
        ret = ioctl(fd, PCIE_SRTR_IOCS_POST_TRG, &postTrigger);
	printf("Sent posttrigger = %d\n", postTrigger/4200000);

        if (ret == -1) {
            fprintf(stderr, "Error: cannot ioctl device %s \n", deviceName);
            goto err;
        }
        ret = ioctl(fd, PCIE_SRTR_IOCT_ACQ_ENABLE);
        if (ret == -1) {
            fprintf(stderr, "Error: cannot ioctl device %s \n", deviceName);
            goto err;
        }
        if(softtrg == 1){
            ret = ioctl(fd, PCIE_SRTR_IOCT_SOFT_TRIG);
	          printf("Sent softtrigger!\n");
            if (ret == -1) {
                fprintf(stderr, "Error: cannot ioctl device %s \n", deviceName);
                goto err;
            }
        }

        i = 0;	
	if(waitTime != 0){
	    printf("Going to wait for %d seconds\n", waitTime);
	    sleep(waitTime);
	}
	else{
            while (i == 0) {
                ret = ioctl(fd, PCIE_SRTR_IOCG_ACQC, &i);
                if (ret < 0) {
                    break;
                }
                sleep(1);
            }
	}
        printf("Acquisition finished. Transferring data!\n");
        ret = ioctl(fd, PCIE_SRTR_IOCT_ACQ_DISABLE);
        if (ret == -1) {
            fprintf(stderr, "Error: cannot ioctl device %s \n", deviceName);
            goto err;
        }
        t0 = time(NULL);
        nbytesClusterSize = nBytes / nOnChannels; //alteraçãp para o fw ver os nbytes como o valor a adquirir por canal
				printf("ClusterSize: %d bytes\n", nbytesClusterSize);
        offsetJump        = 0x80000000 / nOnChannels;
        //reset the offset
        i      = 0;
        offset = 0;
        //just to enter the first time in: if(currentRead > nbytesClusterSize)
        currentRead = nbytesClusterSize + 1;
        while (nBytes > 0) {
            if(currentRead >= nbytesClusterSize){
                currentRead = 0;
                currentChannel++;
                if(outputFD != 0){
                    fclose(outputFD);
                }
                while((channel & (1 << (currentChannel - 1))) == 0){
                    currentChannel++;
                    if(currentChannel > 4)
                        break;
                }
                if(currentChannel > 4){
                     printf("out of channel! Exiting\n");
                     exit(-1);
                }

                if(nOnChannels == 3){
                    if(i == 0)
                        offset = 0;
                    else if(i == 1)
                        offset = 0x20000000; //0x2AAAAAA8;
                    else if(i == 2)
                        offset = 0x40000000; //0x55555550;
                }
                else{
                    offset = i * offsetJump;
                }
                printf("Setting the offset at: 0x%x after reading %d bytes\n", offset, nBytes);
                ret = ioctl(fd, PCIE_SRTR_IOCS_RDOFF, &offset);
                if (ret == -1) {
                    fprintf(stderr, "Error: cannot ioctl device %s \n", deviceName);
                    goto err;
                }
                 
                memset(realFilename, 0, 64);
                sprintf(realFilename, "%s_%d.bin", outputFilename, currentChannel);
								sprintf(filename_dt[cnter], "%s", realFilename);
								cnter++;
                outputFD = fopen(realFilename, "w+");
                i++;
            }
            memset(&buffer, 0, READ_BUFFER_SIZE);
            if (READ_BUFFER_SIZE > nBytes) {
                ret = nBytes;
            } else {
                ret = READ_BUFFER_SIZE;
            }
            ret = read(fd, &buffer, ret);
            if (ret < 1) {
                break;
            }
            if((nbytesClusterSize - currentRead) < 0){
                ret = currentRead;
            }

	    if (outputFD != NULL) {
	        fwrite(&buffer, sizeof(short), ret/sizeof(short), outputFD);
	    }
            nBytes      -= ret;
            currentRead += ret;
        }

        t1 = time(NULL);
        if (outputFD != NULL) {
            fclose(outputFD);
        }

				// split data in ts and pw
				if(DQTP == 2){
					for(z=0; z<nOnChannels; z++){
						printf("splitting data... please wait...\n");
						SRTR_ATCA_splitdata(filename_dt[z], nSamples, PWIDTH);
						printf("done!\n");
					}
				}

    }

    printf("Elapsed wall clock time: %d sec.\n", (int) (t1 - t0));

err:
    printf("Closing device\n");
    close(fd);

    return 0;
}

