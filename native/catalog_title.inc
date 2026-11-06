/* Conservative advances for the pinned Titillium Web Bold title at 35 px.
 * Keep UTF-8 codepoints intact and leave room for an ellipsis in the 580 px field. */
static const unsigned char title_widths[95] = {9,11,16,21,21,21,26,10,12,12,16,21,11,16,10,18,21,21,21,21,21,21,21,21,21,21,10,11,21,21,21,17,36,23,23,20,24,21,20,23,25,12,12,22,18,32,26,24,22,24,23,21,20,24,23,34,21,21,20,14,19,14,21,23,11,19,21,17,21,19,14,20,21,11,11,20,11,31,21,20,21,20,15,18,14,21,19,29,18,19,17,14,11,14,21};
static void catalog_title(const char *text, char *out, int n) {
    if(n<=0)return;
    int width=0,k=0;const unsigned char *p=(const unsigned char*)text;
    while(*p) {
        int bytes=1,advance=36;
        if(*p<128)advance=*p>=32?title_widths[*p-32]:title_widths[0];
        else if((*p&0xe0)==0xc0)bytes=2;
        else if((*p&0xf0)==0xe0)bytes=3;
        else if((*p&0xf8)==0xf0)bytes=4;
        int valid=1;for(int j=1;j<bytes;j++)if(!p[j]||(p[j]&0xc0)!=0x80){valid=0;break;}
        if(!valid)break;
        if(width+advance>548 || k+bytes+4>n)break;
        memcpy(out+k,p,bytes);if(*p<32)out[k]=' ';k+=bytes;p+=bytes;width+=advance;
    }
    if(*p && k+4<=n){memcpy(out+k,"...",3);k+=3;}
    out[k]=0;
}

/* Description: 32-point skin text renders at roughly 22 screen pixels. */
static const unsigned char description_widths[95] = {6,7,10,14,14,14,17,6,8,8,11,14,7,11,7,11,14,14,14,14,14,14,14,14,14,14,7,7,14,14,14,11,23,15,15,13,16,14,13,15,16,7,8,14,12,20,17,16,14,16,15,13,13,16,15,22,14,14,13,9,12,9,14,15,7,13,13,11,13,13,9,13,14,7,7,12,7,20,14,13,13,13,9,12,9,13,12,18,12,12,11,9,7,9,14};
