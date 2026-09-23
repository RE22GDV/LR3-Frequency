// Лабораторна робота №3 — «Захист даних»
// CodinGame: Frequency-Based Decryption
//
// Друга, незалежна реалізація того самого алгоритму мовою C#.
// Призначення — перехресна перевірка: обидві реалізації мають давати
// побітово однаковий результат на всіх п'яти офіційних тестах.
//
// Запуск:
//   dotnet run --project csharp/Freq -- selftest
//   dotnet run --project csharp/Freq < input.txt     (режим CodinGame)
//   dotnet run --project csharp/Freq -- break "Khoor Zruog !"

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace Lab3.Freq;

/// <summary>Шифр Цезаря: зсув лише літер, зі збереженням регістру.</summary>
public static class Caesar
{
    public const int M = 26;

    public static string Shift(string text, int key)
    {
        key = ((key % M) + M) % M;
        var sb = new StringBuilder(text.Length);
        foreach (var ch in text)
        {
            if (ch >= 'A' && ch <= 'Z') sb.Append((char)('A' + (ch - 'A' + key) % M));
            else if (ch >= 'a' && ch <= 'z') sb.Append((char)('a' + (ch - 'a' + key) % M));
            else sb.Append(ch);
        }
        return sb.ToString();
    }

    public static string Encrypt(string text, int key) => Shift(text, key);

    public static string Decrypt(string text, int key) => Shift(text, -key);

    /// <summary>Гістограма 26 літер без урахування регістру.</summary>
    public static int[] LetterCounts(string text)
    {
        var counts = new int[M];
        foreach (var ch in text)
        {
            if (ch >= 'A' && ch <= 'Z') counts[ch - 'A']++;
            else if (ch >= 'a' && ch <= 'z') counts[ch - 'a']++;
        }
        return counts;
    }
}

/// <summary>Злам шифру Цезаря критерієм хі-квадрат.</summary>
public static class Breaker
{
    // Частоти літер, наведені в умові задачі, у відсотках.
    private static readonly double[] Freq =
    {
        8.08, 1.67, 3.18, 3.99, 12.56, 2.17, 1.80, 5.27, 7.24, 0.14, 0.63,
        4.04, 2.60, 7.38, 7.47, 1.91, 0.09, 6.42, 6.59, 9.15, 2.79, 1.00,
        1.89, 0.21, 1.65, 0.07
    };

    /// <summary>
    /// Значення хі-квадрат для кандидата з ключем <paramref name="key"/>.
    /// Замість розшифрування всього тексту зсувається гістограма: це
    /// 26 операцій замість L.
    /// </summary>
    public static double ChiSquared(int[] counts, int total, int key)
    {
        double chi = 0.0;
        for (int i = 0; i < Caesar.M; i++)
        {
            double expected = total * Freq[i] / 100.0;
            int observed = counts[(i + key) % Caesar.M];
            chi += (observed - expected) * (observed - expected) / expected;
        }
        return chi;
    }

    public static int FindKey(string ciphertext)
    {
        var counts = Caesar.LetterCounts(ciphertext);
        int total = 0;
        foreach (var c in counts) total += c;
        if (total == 0) return 0;

        int bestKey = 0;
        double bestChi = double.MaxValue;
        for (int k = 0; k < Caesar.M; k++)
        {
            double chi = ChiSquared(counts, total, k);
            if (chi < bestChi) { bestChi = chi; bestKey = k; }
        }
        return bestKey;
    }

    public static string Break(string ciphertext) =>
        Caesar.Decrypt(ciphertext, FindKey(ciphertext));
}

public static class Program
{
    /// <summary>П'ять офіційних валідаційних тестів CodinGame (скорочені входи).</summary>
    private static readonly (string Label, int Shift, string In, string Out)[] Cases =
    {
        ("Test 1", 3,
         "Khoor Zruog ! Frqjudwxodwlrqv, brx kdyh vxffhvvixoob ghfubswhg ph ! Kdyh ixq zlwk wklv sxccoh",
         "Hello World ! Congratulations, you have successfully decrypted me ! Have fun with this puzzle"),
        ("Test 3", 10,
         "Iye mkx pyyv kvv yp dro zoyzvo cywo yp dro dswo, kxn cywo yp dro zoyzvo kvv yp dro dswo, led iye mkx'd pyyv kvv yp dro zoyzvo kvv yp dro dswo.",
         "You can fool all of the people some of the time, and some of the people all of the time, but you can't fool all of the people all of the time."),
        ("Test 4", 14,
         "Obm qcrs mci'js pssb kfwhwbu tcf 6 acbhvg cf acfs kwhvcih zccywbu oh wh awuvh og kszz vojs pssb kfwhhsb pm gcascbs szgs",
         "Any code you've been writing for 6 months or more without looking at it might as well have been written by someone else")
    };

    public static int Main(string[] args)
    {
        Console.OutputEncoding = Encoding.UTF8;

        if (args.Length > 0 && args[0].Equals("selftest", StringComparison.OrdinalIgnoreCase))
            return SelfTest();

        if (args.Length >= 2 && args[0].Equals("break", StringComparison.OrdinalIgnoreCase))
        {
            Console.WriteLine(Breaker.Break(args[1]));
            return 0;
        }

        if (args.Length >= 3 && args[0].Equals("encrypt", StringComparison.OrdinalIgnoreCase))
        {
            Console.WriteLine(Caesar.Encrypt(args[2],
                int.Parse(args[1], CultureInfo.InvariantCulture)));
            return 0;
        }

        // Режим CodinGame: один рядок зі стандартного входу.
        var message = Console.ReadLine() ?? string.Empty;
        Console.WriteLine(Breaker.Break(message));
        return 0;
    }

    private static int SelfTest()
    {
        Console.WriteLine("Офіційні тести CodinGame (реалізація на C#)");
        Console.WriteLine(new string('-', 78));

        int passed = 0;
        foreach (var (label, shift, input, expected) in Cases)
        {
            int key = Breaker.FindKey(input);
            string got = Caesar.Decrypt(input, key);
            bool ok = got == expected && key == shift;
            if (ok) passed++;
            Console.WriteLine($"[{(ok ? "OK" : "FAIL")}] {label,-7} ключ {key,2} " +
                              $"(істина {shift,2})  {got.Substring(0, Math.Min(42, got.Length))}");
        }

        // Властивість: розшифрування — точна інверсія шифрування.
        var rng = new Random(2026);
        const string pool = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789.,!?'";
        int roundTrips = 0;
        for (int t = 0; t < 2000; t++)
        {
            int len = rng.Next(1, 80);
            var sb = new StringBuilder(len);
            for (int i = 0; i < len; i++) sb.Append(pool[rng.Next(pool.Length)]);
            string msg = sb.ToString();
            int k = rng.Next(Caesar.M);
            if (Caesar.Decrypt(Caesar.Encrypt(msg, k), k) == msg) roundTrips++;
        }

        Console.WriteLine(new string('-', 78));
        Console.WriteLine($"Офіційні тести: пройдено {passed} з {Cases.Length}");
        Console.WriteLine($"Перевірка оборотності: {roundTrips} з 2000 випадкових рядків");
        return passed == Cases.Length && roundTrips == 2000 ? 0 : 1;
    }
}
