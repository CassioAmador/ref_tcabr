#ifndef PCIESRTR_H_
#define PCIESRTR_H_

#ifdef __KERNEL__
#include <linux/module.h>
#else
#define u32 unsigned int
#define dma_addr_t u32
#endif

/*
 * board PCI id 
 */
#define PCI_DEVICE_ID_FPGA	0x08
#define PCIESRTR_MAJOR 252

/*
 * board configurable parameters 
 */
#define DMA_NBYTES  2048  //2048 //1024
#define DMA_BUFFS   16    //Number of DMA Buffs
#define GFPORDER    0
#define WAIT_CYCLES 100
#define IRQ_CYCLES  3

typedef struct _BAR_STRUCT {
    unsigned long start;
    unsigned long end;
    unsigned long len;
    unsigned long flags;

    void* vaddr;
} BAR_STRUCT;

typedef struct _DMA_BUF {
    void* addr_v;
    dma_addr_t addr_hw;
} DMA_BUF;

typedef struct _DMA_STRUCT {
    unsigned int buf_size;
    DMA_BUF buf[DMA_BUFFS];
} DMA_STRUCT;

typedef struct _READ_BUF {
    int dmaCount;
    int total;
    void* buf;    //Assume that ADC data is 32bit wide
    u32 off;      /*Offset 0x64*/
} READ_BUF;

/*
 * BIT ENDIANNESS 
 */
#ifdef __BIG_ENDIAN_BITFIELD
    #define BTFLD(a,b) b,a
#else
    #define BTFLD(a,b) a, b
#endif

/*
 * 8 + 24 bit field 
 */
typedef struct _REVID_FLDS {
    u32 BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(RevId:4, TMR:1), HDR:1), DBG:1), reserved:1),none:24);
} REVID_FLDS;
/*
 * 24 + 8 bit field
 */
typedef struct _STATUS_FLDS {
    u32 BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(
                BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(none:8, rsv0:8), rsv1:2),
                FSH:1), RST:1), rsv2:2), ERR1:1), ERR0:1), rsv3:2),
                FIFE:1), FIFF:1), rsv4:2), DMAC:1), ACQC:1);
} STATUS_FLDS;


typedef struct _STATUS_REG {
    union {
        u32 reg32;
        struct _STALFD {
            u32 revId:8;
            u32 statWrd:24;
        } Str;
        STATUS_FLDS statFlds;
        REVID_FLDS rdIdFlds;
    };
} STATUS_REG;

/*
 * 32 bit reg 
 */
typedef struct _COMMAND_REG {
    union{
        u32 reg32;
        struct  {
                u32 BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(
                    BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(BTFLD(rsv0:1, COMPL:1), LOAD:1), ACQM:1), DQTP:2), CH1_ACT:1), CH2_ACT:1), CH3_ACT:1), CH4_ACT:1), ILVM:2), PLLCFG:4), 
                    rsv2:2), HOP:1), TOP:1), ACQS:1), ACQT:1), ACQK:1), ACQE:1), STRG:1), rsv3:1), DMAF:1), DMAE:1), 
                    rsv4:1), ERRiE:1), DMAiE:1), ACQiE:1);
        } cmdFlds;
    };    
} COMMAND_REG;

/*
 * 32 bit reg 
 */
typedef struct _DATA_PROC_REG {
    union
    {
        u32 reg32;
        struct  {
                u32 BTFLD(BTFLD(BTFLD(K:4, L:8), M:16),T:4);
        } dpFlds;
    };
} DATA_PROC_REG;

/*
 * 32 bit reg 
 */
typedef struct _DMA_REG {
    union
    {
        u32 reg32;
        struct  {
            u32 BTFLD(Size:16, BuffsNumber:16);
        } dmaFlds;
    };
} DMA_REG;

/*
 * 32 bit reg for post trigger dat
 */
typedef struct _PRE_TRG_DATA_REG {
    union
    {
        u32 reg32;
        struct  {
            u32 BTFLD(BTFLD(BTFLD(PTRG:8, PWIDTH:16), Trg_Acc:2), Generic:6);
        } ptdFlds;
    };
} PRE_TRG_DATA_REG;

typedef struct _PCIE_HREGS {
    volatile STATUS_REG       status;
    volatile COMMAND_REG      command;            /*Offset 0x04*/
    volatile u32              postTriggerTime;    /*Offset 0x08*/
    volatile DMA_REG          dmaReg;             /*Offset 0x0C*/
    volatile u32              dmaCurrBuff;        /*Offset 0x10*/
    volatile u32              hwcounter;          /*Offset 0x14*/
    volatile u32              _reserved1;         /*Offset 0x18*/
    volatile u32              FileParameter;      /*Offset 0x1C*/
    volatile u32              HwDmaAddr[16];      /*Offset 0x20 - 0x5C*/
    volatile u32              dmaNbytes;          /*Offset 0x60*/
    volatile u32              dmaOffSet;          /*Offset 0x64*/
    volatile DATA_PROC_REG    dpReg;              /*Offset 0x68*/
    volatile PRE_TRG_DATA_REG preTrigerDataReg;   /*Offset 0x6C*/
    volatile u32              acqByteSize;        /*Offset 0x70 - Default=0x4000000 (64Mb)*/
} PCIE_HREGS;

#ifdef __KERNEL__
typedef struct _PCIE_DEV {
    //char device
    struct cdev     cdev;         //linux char device structure 
    dev_t           devno;        //char first device number
    struct pci_dev *pdev;         //pci device
    unsigned char   irq;
    spinlock_t      irq_lock;     //static
    unsigned int    counter;
    unsigned int    counter_hw;
    unsigned        open_count;
    unsigned        acqc;
    struct semaphore open_sem;    //mutual exclusion semaphore
    wait_queue_head_t rd_q;       //read  queues
    long wt_tmout;                //read timeout
    unsigned long size;           //TODO: max amount  of data stored in memory
    BAR_STRUCT memIO[2];
    DMA_STRUCT dmaIO;
    READ_BUF bufRD;               // buffer struct for read() ops
    PCIE_HREGS *pHregs;
} PCIE_DEV ;
#endif//__KERNEL__

#endif /*PCIESRTR_H_*/
