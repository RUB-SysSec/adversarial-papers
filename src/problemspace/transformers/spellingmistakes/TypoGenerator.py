import re


class TypoGenerator:
    """
    Common english typos.
    """

    typo = [
        ["\\Bal(ly)$", "ends with -ally", [["al"], "", "\\1"]],
        ["\\B(cc.*)(m)(m)\\B", "two cs, two ms", [["m"], "\\1", "", "\\3"]],
        ["\\B(ie)\\B", "i before e", [["ie"], "\\0", "ei"]],
        ["([^c])(c)([^c])", "one c", [["c"], "\\1", "cc", "\\3"]],
        ["\\Bg(g)\\B", "two gs", [["g"], "", "\\1"]],
        ["\\Be(ntly)$", "-ent not -ant", [["e"], "a", "\\1"]],
        ["\\Be(nt)$", "ends with -ent", [["e"], "a", "\\1"]],
        ["\\Ba(nce)$", "ends with -ance", [["a"], "e", "\\1"]],
        ["\\B(u)\\B", "no e after the u", [["u"], "\\0", "ue"]],
        ["\\B(ss.*)(s)(s)\\B", "two double s’s", [["s"], "\\1", "", "\\3"]],
        ["\\B(n)(n)(ing)$", "double n before the -ing", [["n"], "\\1", "", "\\3"]],
        ["\\B([^z])(z)([^zr]r)(r)\\B", "one z, double -r", [["z", "r"], "\\1", "zz", "\\3", ""]],
        ["(^bu)(si)", "begins with busi-", [["si"], "\\1", "is"]],
        ["\\Ba(r)$", "-ar not -er", [["a"], "e", "\\1"]],
        ["\\B([^r])(r)([^rb]b)(b)\\B", "one r, two bs", [["r", "b"], "\\1", "rr", "\\3", ""]],
        ["\\Be(ry)", "ends with -ery", [["e"], "a", "\\1"]],
        ["\\B(e)(u)(r)$", "ends with -eur", [["u"], "\\1", "", "\\3"]],
        ["\\B(e)(a)\\B", "-ea- in the middle", [["a"], "\\1", ""]],
        ["\\B([^m])(m)(ing)", "one m", [["m"], "\\1", "mm", "\\3"]],
        ["\\B(mm[^mt])(t)(tee)", "double m, double t, double e", [["t"], "\\1", "", "\\3"]],
        ["\\Be(ly)", "ends with -ely", [["e"], "", "\\1"]],
        ["\\B(s)(c)\\B", "-sc- in the middle", [["s"], "", "\\2"]],
        ["\\B(o)(s)\\B", "-os- in the middle", [["o"], "ou", "\\2"]],
        ["\\Bi(te)", "-ite- not –ate-", [["i"], "a", "\\1"]],
        ["\\B(m)(m)\\B", "-mm- not -mn-", [["m"], "\\1", "n"]],
        ["\\B([^s])(s)([^sp]p)(p)\\B", "one s, two ps", [["s", "p"], "\\1", "ss", "\\3", ""]],
        ["\\Bs(y)$", "ends with –sy", [["s"], "c", "\\1"]],
        ["\\B(r)(r)(.*ss)\\B", "two rs, two s’s", [["r"], "\\1", "", "\\3"]],
        ["\\B(n)(m)\\B", "n before the m", [["n"], "", "\\2"]],
        ["\\Be(nce)$", "ends with -ence", [["e"], "a", "\\1"]],
        ["(^Fa)(h)(r)", "begins with Fahr-", [["h"], "\\1", "", "\\3"]],
        ["\\Bi(ar)$", "ends with -iar", [["i"], "", "\\1"]],
        ["\\Bl(l)\\B", "two ls", [["l"], "", "\\1"]],
        ["(^fl)(u)(or)", "begins with fluor-", [["u"], "\\1", "", "\\3"]],
        ["\\B(ei)\\B", "e before i", [["ei"], "\\0", "ie"]],
        ["(^for)(e)", "begins with fore-", [["e"], "\\1", ""]],
        ["(^fo)(r)", "begins with for-", [["r"], "\\1", "ur"]],
        ["(^fo)(r)", "begins with for-", [["r"], "\\1", ""]],
        ["(^fu)(r)", "begins with fur-", [["r"], "\\1", ""]],
        ["(^g)", "begins with g-", [["g"], "\\0", "j"]],
        ["\\B(m)(o)(r)\\B", "-mor- in the middle", [["o"], "\\1", "ou", "\\3"]],
        ["(^g)(ua)", "begins with gua-", [["ua"], "\\1", "au"]],
        ["(en)(e)(d)$", "ends with -ened", [["e"], "\\1", "", "\\3"]],
        ["\\B([^r])(r)([^rs]ss)", "one r, two s’s", [["r"], "\\1", "rr", "\\3"]],
        ["\\B(n)(o)(r)\\B", "-nor- in the middle", [["o"], "\\1", "ou", "\\3"]],
        ["\\Br(r)\\B", "two rs", [["r"], "", "\\1"]],
        ["\\Bi(ble)$", "ends with -ible", [["i"], "a", "\\1"]],
        ["\\B(d)\\B", "remember the d", [["d"], "\\0", ""]],
        ["(^lia)(i)(s)", "remember the second i: liais-", [["i"], "\\1", "", "\\3"]],
        # ["\\B(i)\\B", "i in the middle", [["i"], "\\0", "y"]],
        ["\\B(ll.*)(n)(n)\\B", "double l, double n", [["n"], "\\1", "", "\\3"]],
        ["\\B(t)(h)(al)$", "ends with -thal", [["h"], "\\1", "", "\\3"]],
        ["\\B([^c])(c)(.*ss)\\B", "one c, two s’s", [["c"], "\\1", "cc", "\\3"]],
        ["\\B(e)\\B", "remember the middle e", [["e"], "\\0", ""]],
        ["\\B(cc.*[^s])(s)([^s])\\B", "two cs, one s", [["s"], "\\1", "ss", "\\3"]],
        ["\\B(cc.*)(r)(r)\\B", "two cs, two rs", [["r"], "\\1", "", "\\3"]],
        ["\\B([^l])(l)([^l])\\B", "one l", [["l"], "\\1", "ll", "\\3"]],
        ["\\Bao(h)$", "ends with -aoh", [["ao"], "oa", "\\1"]],
        ["\\B(c)(i)(an)$", "ends with -cian", [["i"], "\\1", "", "\\3"]],
        ["\\B(g)(u)(ese)$", "ends with –guese", [["u"], "\\1", "", "\\3"]],
        ["\\B(s)(s)(.*ss)\\B", "two s’s in the middle and two at the end", [["s"], "\\1", "", "\\3"]],
        ["(^prop)(a)", "begins with propa-", [["a"], "\\1", "o"]],
        ["\\Bc(ly)$", "ends with –cly", [["c"], "cal", "\\1"]],
        ["\\B(g)(i)(ous)$", "ends with -gious", [["i"], "\\1", "", "\\3"]],
        ["\\B(me)(m)\\B", "-mem- in the middle", [["m"], "\\1", ""]],
        ["\\Bs(e)$", "ends with -se", [["s"], "c", "\\1"]],
        ["\\B(p)(a)(r)\\B", "-par- in the middle", [["a"], "\\1", "e", "\\3"]],
        ["\\B(cc.*)(s)(s)\\B", "two cs, two s’s", [["s"], "\\1", "", "\\3"]],
        ["\\Bs(ede)$", "ends with -sede", [["s"], "c", "\\1"]],
        ["(^su)(r)", "begins with sur-", [["r"], "\\1", ""]],
        ["\\B(t)(t)(oo)", "two ts, two os", [["t"], "\\1", "", "\\3"]],
        ["\\Be(ncy)$", "ends with -ency", [["e"], "a", "\\1"]],
        ["(for)(e)$", "ends with -fore", [["e"], "\\1", ""]],
        # ["([^th])(h)([^h])", "one h in the middle", [["h"], "\\1", "hh", "\\3"]],
        ["\\B([^m])(m)([^m])(.*rr)\\B", "one m, two rs", [["m"], "\\1", "mm", "\\3\\4"]],
        ["\\B(for)(e)\\B", "remember the e after the r", [["e"], "\\1", ""]],
        ["\\B([^l])(l)$", "one l at the end", [["l"], "\\1", "ll"]],
        # ["([^he])(e)([^er])", "one e in the middle", [["e"], "\\1", "ee", "\\3"]],
        ["(^w)(h)", "begins with wh-", [["h"], "\\1", ""]],
        ["\\B(r)(re)(nce)$", "two cs, two rs, -ence not -ance", [["re"], "\\1", "a", "\\3"]],
        ["(^t)(o)(n.*g)(u)(e)$", "begins with ton-, ends with -gue", [["o", "u"], "\\1", "ou", "\\3", "", "\\5"]]
    ]

    def getstartpos(self, w1, w2):
        l = len(w2)
        for i in range(len(w1)):
            if i <= l - 1:
                if w1[i] == w2[i]:
                    pass
                else:
                    return i
            else:
                return i
        if len(w1) < len(w2):
            return len(w1) - 1

    def gettypo(self, word):
        all_misspellings = []
        for t in self.typo:
            misspelling = ""
            pos = []
            if re.findall(t[0], word):
                rpl = ""
                rpl_word = []
                for r in t[2][1:]:
                    rpl += r
                    if "\\" not in r:
                        rpl_word.append(r)

                misspelling = re.sub(t[0], rpl, word).replace("\x00", "")

                start_pos = 0
                en_pos = 0
                if len(t[2][0]) == len(rpl_word):
                    try:
                        start_pos = self.getstartpos(word, misspelling) + 1
                        end_pos = start_pos

                        for i in range(len(rpl_word)):
                            if len(t[2][0][i]) > len(rpl_word[i]):
                                end_pos = (len(t[2][0][i]) - len(rpl_word[i])) + start_pos - 1

                            elif len(t[2][0][i]) == len(rpl_word[i]):
                                end_pos = start_pos + len(rpl_word[i]) - 1

                            pos.append((start_pos, end_pos))

                            try:
                                start_pos = self.getstartpos(word[start_pos:], misspelling[start_pos + len(
                                    rpl_word[i]) - 1:]) + start_pos + 1

                            except TypeError:
                                pass
                    except TypeError:
                        pass

                all_misspellings.append((misspelling, pos, t[1]))

        return all_misspellings


if __name__ == "__main__":
    test = ["basically", "accommodate", "accommodation", "achieve", "across",
            "wherever", "which"]

    tg = TypoGenerator()

    for w in test:
        print("WORD: " + w)
        print(tg.gettypo(w))
        print("#########")