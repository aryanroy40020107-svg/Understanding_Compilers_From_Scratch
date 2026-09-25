#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdarg.h>

typedef enum {
    LE, NE, LT, EQ, GE, GT, ERR
} TokenType;

void log_trace(FILE *log_file, const char *format, ...) {
    if (log_file != NULL) {
        va_list args;
        va_start(args, format);
        vfprintf(log_file, format, args);
        va_end(args);
    }
}

TokenType get_relational_token(const char *input, int *index, int *lexeme_len, FILE *log_file) {
    int state = 0;
    char c;
    int start_index = *index;
    char lookahead_char;

    while (1) {
        switch (state) {
            case 0:
                c = input[(*index)++];
                if (c == '\0') {
                    (*index)--;
                    return ERR;
                }
                if (c == '<') state = 1;
                else if (c == '=') state = 5;
                else if (c == '>') state = 6;
                else {
                    *lexeme_len = 1;
                    log_trace(log_file, "%c (State 0 -> Err): Invalid initial character.\n", c);
                    return ERR;
                }
                break;

            case 1:
                lookahead_char = input[*index];
                c = input[(*index)++];
                if (c == '=') {
                    *lexeme_len = *index - start_index;
                    log_trace(log_file, "<= (State 0 -> 1 -> 2): Consumes two characters, matches perfectly, returns LE.\n");
                    return LE;
                } else if (c == '>') {
                    *lexeme_len = *index - start_index;
                    log_trace(log_file, "<> (State 0 -> 1 -> 3): Consumes two characters, matches perfectly, returns NE.\n");
                    return NE;
                } else {
                    if (c != '\0') (*index)--; 
                    *lexeme_len = *index - start_index;
                    log_trace(log_file, "< (State 0 -> 1 -> Retract): Reads < then looks ahead at the space '%c'. Because space doesn't match = or >, it retracts the index by 1 so the space isn't lost, drops to State 4, and returns LT.\n", lookahead_char);
                    return LT;
                }
                break;

            case 5:
                lookahead_char = input[*index];
                c = input[(*index)++];
                if (c == '=') {
                    *lexeme_len = *index - start_index;
                    log_trace(log_file, "== (State 0 -> 5 -> 9): Consumes two characters, matches perfectly, returns EQ.\n");
                    return EQ;
                } else {
                    if (c != '\0') (*index)--;
                    *lexeme_len = *index - start_index;
                    log_trace(log_file, "= (State 0 -> 5 -> Retract): Reads = then looks ahead at the space '%c'. It retracts the index back by 1, fails, and returns ERR.\n", lookahead_char);
                    return ERR;
                }
                break;

            case 6:
                lookahead_char = input[*index];
                c = input[(*index)++];
                if (c == '=') {
                    *lexeme_len = *index - start_index;
                    log_trace(log_file, ">= (State 0 -> 6 -> 7): Consumes two characters, matches perfectly, returns GE.\n");
                    return GE;
                } else {
                    if (c != '\0') (*index)--;
                    *lexeme_len = *index - start_index;
                    log_trace(log_file, "> (State 0 -> 6 -> Retract): Reads > and looks ahead at the space '%c'. It retracts the index back by 1, drops to State 8, and returns GT.\n", lookahead_char);
                    return GT;
                }
                break;
        }
    }
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Error: No input stream provided as argument.\n");
        return 1;
    }

    const char *input_stream = argv[1];
    
    // Explicit WSL Absolute Destination Path Configuration
    FILE *log_file = fopen("/mnt/d/btech_jgec/2026-27/compiler_lab/compiler1/lexer_trace.txt", "w");
    if (log_file == NULL) {
        printf("Error creating trace log file!\n");
        return 1;
    }

    int index = 0;
    printf("\n%-15s %-15s\n", "LEXEME", "TOKEN");
    printf("-------------------------------\n");

    while (input_stream[index] != '\0') {
        if (isspace((unsigned char)input_stream[index])) {
            index++;
            continue;
        }

        int lexeme_len = 0;
        int current_start = index;
        
        TokenType token = get_relational_token(input_stream, &index, &lexeme_len, log_file);

        char lexeme[20];
        if (lexeme_len >= 20) lexeme_len = 19;
        strncpy(lexeme, &input_stream[current_start], lexeme_len);
        lexeme[lexeme_len] = '\0';

        printf("%-15s ", lexeme);
        switch (token) {
            case LE: printf("LE (<=)\n"); break;
            case NE: printf("NE (<>)\n"); break;
            case LT: printf("LT (<)\n"); break;
            case EQ: printf("EQ (==)\n"); break;
            case GE: printf("GE (>=)\n"); break;
            case GT: printf("GT (>)\n"); break;
            default: printf("ERR\n"); break;
        }
    }

    fclose(log_file);
    return 0;
}
