"""
CodinGame - "Frequency-Based Decryption" (Medium)
https://www.codingame.com/training/medium/frequency-based-decryption

Self-contained solution, submitted as-is.
This file is kept ASCII-only and byte-identical to the accepted submission;
the Ukrainian write-up lives in README.md and in src/freqcrack/.

Task: an English text was encrypted with a Caesar shift. The key is NOT
given. Recover it by letter-frequency analysis and print the plaintext,
preserving letter case and leaving non-alphabetic characters untouched.

Method: the key space has only 26 elements, so this is a decision problem
rather than a search. Every candidate shift is scored with the chi-squared
statistic against the reference frequency table supplied by the puzzle,
and the candidate with the smallest value wins.

    chi2(k) = sum over letters of (observed - expected)^2 / expected

Time O(26 * L), extra memory O(26).
"""

import sys

# Reference letter frequencies, in percent, exactly as given in the puzzle.
FREQ = [8.08, 1.67, 3.18, 3.99, 12.56, 2.17, 1.80, 5.27, 7.24, 0.14, 0.63,
        4.04, 2.60, 7.38, 7.47, 1.91, 0.09, 6.42, 6.59, 9.15, 2.79, 1.00,
        1.89, 0.21, 1.65, 0.07]

M = 26


def main() -> None:
    message = sys.stdin.readline().rstrip("\n")

    # Letter histogram of the ciphertext, case-insensitive.
    counts = [0] * M
    total = 0
    for ch in message:
        if "A" <= ch <= "Z":
            counts[ord(ch) - 65] += 1
            total += 1
        elif "a" <= ch <= "z":
            counts[ord(ch) - 97] += 1
            total += 1

    # Score every possible shift; shifting the histogram is equivalent to
    # decrypting the whole message, but costs 26 operations instead of L.
    best_key, best_chi = 0, None
    for k in range(M):
        chi = 0.0
        for i in range(M):
            expected = total * FREQ[i] / 100.0
            observed = counts[(i + k) % M]
            chi += (observed - expected) ** 2 / expected
        if best_chi is None or chi < best_chi:
            best_key, best_chi = k, chi

    # Decrypt with the winning key, preserving case and non-letters.
    out = []
    for ch in message:
        if "A" <= ch <= "Z":
            out.append(chr((ord(ch) - 65 - best_key) % M + 65))
        elif "a" <= ch <= "z":
            out.append(chr((ord(ch) - 97 - best_key) % M + 97))
        else:
            out.append(ch)

    print("".join(out))


if __name__ == "__main__":
    main()
