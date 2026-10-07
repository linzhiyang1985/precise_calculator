# -*- coding: utf-8 -*-
import PySimpleGUI as sg
import re
sg.theme('LightBlue')

"""
无限位数计算器
================
用字符串/数组存储每一位数字，模拟小学竖式手算，实现任意精度的
加、减、乘、除，支持小数。

数据结构
--------
BigDecimal 内部用三段表示一个数：
    sign            : 符号，+1 或 -1
    digits          : 数字数组，最低位(LSB， Least Significant Bit)在前，方便从右往左逐位运算
    decimal_places  : 小数点后的位数

例如 123.45  ->  sign=1, digits=[5,4,3,2,1], decimal_places=2
其数值等价于 整数 12345 / 10^2
"""

class CalculatorGUI:
    def __init__(self):
        self.window = sg.Window('无限位数计算器', [
            [sg.Text('第一个数:'), sg.Input(key='first_num', enable_events=True, tooltip='只允许数字和小数点，[Delete]清空输入')],
            [sg.Text('第二个数:'), sg.Input(key='second_num', enable_events=True, tooltip='只允许数字和小数点，[Delete]清空输入')],
            [sg.Text('运算符:'), sg.Radio('+', key='opt_add', group_id='operator', default=True),
                                sg.Radio('-', key='opt_sub', group_id='operator'),
                                sg.Radio('*', key='opt_mul', group_id='operator'),
                                sg.Radio('/', key='opt_div', group_id='operator')],
            [sg.Button('计算', key='calculate')],
            [sg.Text('精度位数:'), sg.Slider(range=(0, 100), default_value=4, key='precision', orientation='h')],
            [sg.Text('等于:'), sg.Input(key='result', readonly=True, default_text='...')]
        ],
        titlebar_background_color='Blue', titlebar_font=('Helvetica', 16), font=('Helvetica', 14),
        return_keyboard_events=True, finalize=True, print_event_values=False)
        self._event_loop_()
        self.NUMBER

    def _event_loop_(self):
        """事件循环，处理用户输入。"""
        while True:
            event, values = self.window.read()
            if event == sg.WIN_CLOSED:
                break

            if self.window.find_element_with_focus().key in ('first_num', 'second_num'):
                focused_elem = self.window.find_element_with_focus()
                if event.startswith('Delete'):
                    focused_elem.update('')
                else:
                    not_allowed_chars = '[^0123456789.+-]'
                    origin_value = values[focused_elem.key]
                    removed_illegal_chars = re.sub(not_allowed_chars, '', origin_value)
                    
                    if removed_illegal_chars.count('.') > 1:
                        int_part, other_part = removed_illegal_chars.split('.', maxsplit=1)
                        removed_illegal_chars = int_part + '.' + other_part.replace('.', '')
                    
                    if removed_illegal_chars.find('+') > 0:
                        removed_illegal_chars = removed_illegal_chars[0] + removed_illegal_chars[1:].replace('+', '')
                    if removed_illegal_chars.find('-') > 0:
                        removed_illegal_chars = removed_illegal_chars[0] + removed_illegal_chars[1:].replace('-', '')
                    
                    if origin_value != removed_illegal_chars:
                        self.window[focused_elem.key].update(removed_illegal_chars)
            else:
                if event.startswith('KP_Add') or event.startswith('plus'):
                    self.window['opt_add'].update(True)
                elif event.startswith('KP_Subtract') or event.startswith('minus'):
                    self.window['opt_sub'].update(True)
                elif event.startswith('KP_Multiply') or event.startswith('asterisk'):
                    self.window['opt_mul'].update(True)
                elif event.startswith('KP_Divide') or event.startswith('slash'):
                    self.window['opt_div'].update(True)
                
                if event.startswith('Right'):
                    self.window['precision'].update(values['precision'] + 1)
                elif event.startswith('Left'):
                    self.window['precision'].update(values['precision'] - 1)

            if event == 'calculate' or event.startswith('KP_Enter') or event.startswith('Return'):
                self._handle_calculate(values)
        self.window.close()
    
    def _handle_calculate(self, values):
        """处理计算按钮点击事件。"""
        first_num = BigDecimal(values['first_num'], div_precision=int(values['precision']))
        second_num = BigDecimal(values['second_num'], div_precision=int(values['precision']))
        if values['opt_add']:
                result = first_num + second_num
        elif values['opt_sub']:
                result = first_num - second_num
        elif values['opt_mul']:
                result = first_num * second_num
        elif values['opt_div']:
                result, remainder = first_num / second_num
                if remainder != BigDecimal(0):
                    result = f'{result}...{remainder}'
        else:
                result = '...'
        self.window['result'].update(str(result))


class BigDecimal:
    """任意精度十进制小数。"""

    # ------------------------------------------------------------------ #
    # 构造与解析
    # ------------------------------------------------------------------ #
    def __init__(self, value, div_precision=4):
        if isinstance(value, BigDecimal):
            self.sign = value.sign
            self.digits = list(value.digits)
            self.decimal_places = value.decimal_places
        else:
            self._parse(str(value).strip())
        self.div_precision = div_precision

    def _parse(self, s):
        self.sign = 1
        if s and s[0] in '+-':
            if s[0] == '-':
                self.sign = -1
            s = s[1:]

        if '.' in s:
            int_part, frac_part = s.split('.', 1)
            frac_part = frac_part.rstrip('0')        # 去掉小数末尾的 0
            self.decimal_places = len(frac_part)
            digit_str = (int_part + frac_part).lstrip('0')
        else:
            self.decimal_places = 0
            digit_str = s.lstrip('0')

        if not digit_str:
            digit_str = '0'
        if digit_str == '0':
            self.sign = 1

        # 最低位在前
        self.digits = [int(c) for c in reversed(digit_str)]

    @staticmethod
    def _from_digits(digits_lsb, sign, decimal_places):
        """从 LSB 数字数组构造对象，并做规范化（去掉前导/末尾零）。"""
        if decimal_places < 0:
            # 小数位为负，相当于整体乘以 10 的正幂，高位补零
            digits_lsb = digits_lsb + [0] * (-decimal_places)
            decimal_places = 0

        # 去掉小数末尾的 0（数组最前端）
        while decimal_places > 0 and len(digits_lsb) > 0 and digits_lsb[0] == 0:
            digits_lsb.pop(0)
            decimal_places -= 1

        # 去掉整数部分高位的 0（数组最后端）
        while len(digits_lsb) > 1 and digits_lsb[-1] == 0:
            digits_lsb.pop()

        if not digits_lsb:
            digits_lsb = [0]
            decimal_places = 0
            sign = 1

        obj = object.__new__(BigDecimal)
        obj.sign = sign if digits_lsb != [0] else 1
        obj.digits = digits_lsb
        obj.decimal_places = decimal_places
        return obj

    # ------------------------------------------------------------------ #
    # 输出
    # ------------------------------------------------------------------ #
    def _to_int_str(self):
        """忽略小数点，返回整数部分的字符串（MSB(Most Significant Bit) 在前）。"""
        return ''.join(str(d) for d in reversed(self.digits))

    def __str__(self):
        int_str = self._to_int_str()
        if self.decimal_places == 0:
            s = int_str
        else:
            if len(int_str) <= self.decimal_places:
                int_str = '0' * (self.decimal_places - len(int_str) + 1) + int_str
            s = int_str[:-self.decimal_places] + '.' + int_str[-self.decimal_places:]
        if self.sign == -1 and s != '0':
            s = '-' + s
        return s

    def __repr__(self):
        return f"BigDecimal('{self}')"

    def __eq__(self, other):
        return str(self) == str(other)

    # ------------------------------------------------------------------ #
    # 无符号数组运算（LSB 在前）
    # ------------------------------------------------------------------ #
    @staticmethod
    def _add_unsigned(d1, d2):
        result = []
        carry = 0
        n = max(len(d1), len(d2))
        for i in range(n):
            s = carry
            if i < len(d1):
                s += d1[i]
            if i < len(d2):
                s += d2[i]
            result.append(s % 10)
            carry = s // 10
        if carry:
            result.append(carry)
        return result

    @staticmethod
    def _sub_unsigned(d1, d2):
        """无符号减法，要求 d1 >= d2。"""
        result = []
        borrow = 0
        for i in range(len(d1)):
            d = d1[i] - borrow
            if i < len(d2):
                d -= d2[i]
            if d < 0:
                d += 10
                borrow = 1
            else:
                borrow = 0
            result.append(d)
        while len(result) > 1 and result[-1] == 0:
            result.pop()
        return result

    @staticmethod
    def _compare_unsigned(d1, d2):
        # d1,d2已对齐小数位长度，且是LSB格式
        if len(d1) != len(d2):
            return 1 if len(d1) > len(d2) else -1
        #相同长度，从右(高位)往左逐位比较
        for i in range(len(d1) - 1, -1, -1):
            if d1[i] != d2[i]:
                return 1 if d1[i] > d2[i] else -1
        return 0

    @staticmethod
    def _mul_unsigned(d1, d2):
        if d1 == [0] or d2 == [0]:
            return [0]
        result = [0] * (len(d1) + len(d2))
        for i in range(len(d1)):
            carry = 0
            for j in range(len(d2)):
                s = result[i + j] + d1[i] * d2[j] + carry
                result[i + j] = s % 10
                carry = s // 10
            result[i + len(d2)] += carry
        while len(result) > 1 and result[-1] == 0:
            result.pop()
        return result

    @staticmethod
    def _align(a, b):
        """对齐小数点：两者都补零到相同的小数位数。"""
        max_dp = max(a.decimal_places, b.decimal_places)
        # 应为digits按LSB格式存储，所以0补在数组前面， 头max_dp位属于小数部分
        a_digits = [0] * (max_dp - a.decimal_places) + a.digits
        b_digits = [0] * (max_dp - b.decimal_places) + b.digits
        return a_digits, b_digits, max_dp

    # ------------------------------------------------------------------ #
    # 四则运算
    # ------------------------------------------------------------------ #
    def add(self, other):
        """加法。"""
        other = BigDecimal(other)
        self_digits, other_digits, common_decimal_places = self._align(self, other)
        if self.sign == other.sign:
            result_digits = self._add_unsigned(self_digits, other_digits)
            result_sign = self.sign
        else:
            cmp = self._compare_unsigned(self_digits, other_digits)
            if cmp == 0:
                return BigDecimal('0')
            elif cmp > 0:
                result_digits = self._sub_unsigned(self_digits, other_digits)
                result_sign = self.sign
            else:
                result_digits = self._sub_unsigned(other_digits, self_digits)
                result_sign = other.sign
        return self._from_digits(result_digits, result_sign, common_decimal_places)

    def sub(self, other):
        """减法。"""
        other = BigDecimal(other)
        other.sign = -other.sign
        return self.add(other)

    def mul(self, other):
        """乘法：竖式逐位相乘后累加。"""
        other = BigDecimal(other)
        result_digits = self._mul_unsigned(self.digits, other.digits)
        result_dp = self.decimal_places + other.decimal_places
        result_sign = self.sign * other.sign
        return self._from_digits(result_digits, result_sign, result_dp)

    # ---- 除法需要 MSB 在前的辅助函数 ---- #
    @staticmethod
    def _mul_int_by_digit(msb_digits, one_digit):
        if one_digit == 0:
            return [0]
        result = []
        carry = 0
        for i in range(len(msb_digits) - 1, -1, -1):
            s = msb_digits[i] * one_digit + carry
            result.append(s % 10) # LSB
            carry = s // 10
        if carry:
            result.append(carry)
        result.reverse() # MSB
        return result

    @staticmethod
    def _compare_msb(a, b):
        while len(a) > 1 and a[0] == 0:
            a = a[1:]
        while len(b) > 1 and b[0] == 0:
            b = b[1:]
        if len(a) != len(b):
            return 1 if len(a) > len(b) else -1
        for i in range(len(a)):
            if a[i] != b[i]:
                return 1 if a[i] > b[i] else -1
        return 0

    @staticmethod
    def _sub_msb(a, b):
        """MSB 在前的无符号减法，要求 a >= b。"""
        result = []
        borrow = 0
        offset = len(a) - len(b)
        for i in range(len(a) - 1, -1, -1):
            d = a[i] - borrow
            if i >= offset:
                d -= b[i - offset]
            if d < 0:
                d += 10
                borrow = 1
            else:
                borrow = 0
            result.append(d)
        result.reverse()
        while len(result) > 1 and result[0] == 0:
            result.pop(0)
        return result

    @staticmethod
    def _divmod_int(dividend_msb, divisor_msb):
        """两个正整数的长除法，返回 (商, 余数)，均为 MSB 在前。"""
        quotient = []
        remainder = []
        for digit in dividend_msb:
            remainder.append(digit)
            while len(remainder) > 1 and remainder[0] == 0:
                remainder.pop(0) # 移除最高位的0
            q = 0
            for trial in range(9, -1, -1):
                # 从大到小试商
                prod = BigDecimal._mul_int_by_digit(divisor_msb, trial)
                if BigDecimal._compare_msb(prod, remainder) <= 0: # prod smaller or equal to remainder
                    q = trial
                    break
            quotient.append(q)
            sub = BigDecimal._mul_int_by_digit(divisor_msb, q)
            remainder = BigDecimal._sub_msb(remainder, sub)
        while len(quotient) > 1 and quotient[0] == 0:
            quotient.pop(0)
        return quotient, remainder

    def div(self, other, precision=20):
        """
        除法：长除法 + 逐位试商。
        precision : 保留的小数位数（除不尽时）。
        """
        other = BigDecimal(other)
        if other.digits == [0]:
            raise ZeroDivisionError("division by zero")

        # self = S / 10^a_dp, other = O / 10^o_dp
        # result = (S / O) * 10^(o_dp - a_dp)
        s_msb = self.digits[::-1]
        o_msb = other.digits[::-1]

        quotient_int, remainder = self._divmod_int(s_msb, o_msb)

        fractional = []
        rem = remainder[:]
        for _ in range(precision):
            rem.append(0)                      # 余数 × 10
            while len(rem) > 1 and rem[0] == 0:
                rem.pop(0)
            q = 0
            for trial in range(9, -1, -1):     # 从 9 往下试商
                prod = self._mul_int_by_digit(o_msb, trial)
                if self._compare_msb(prod, rem) <= 0:
                    q = trial
                    break
            fractional.append(q)
            sub = self._mul_int_by_digit(o_msb, q)
            rem = self._sub_msb(rem, sub)
            if rem == [0]:                     # 除尽，后面补 0
                fractional.extend([0] * (precision - len(fractional)))
                break

        # 合并整数与小数部分，MSB 在前
        result_msb = quotient_int + fractional
        result_digits = result_msb[::-1]
        # 结果小数位数 = 计算精度 - (o_dp - a_dp)
        result_dp = precision - (other.decimal_places - self.decimal_places)

        result_sign = self.sign * other.sign
        result_quotient = self._from_digits(result_digits, result_sign, result_dp)
        result_remainder = self.sub(result_quotient.mul(other))
        return result_quotient, result_remainder

    # ------------------------------------------------------------------ #
    # 运算符重载
    # ------------------------------------------------------------------ #
    def __add__(self, other):
        return self.add(other)

    def __radd__(self, other):
        return BigDecimal(other).add(self)

    def __sub__(self, other):
        return self.sub(other)

    def __rsub__(self, other):
        return BigDecimal(other).sub(self)

    def __mul__(self, other):
        return self.mul(other)

    def __rmul__(self, other):
        return BigDecimal(other).mul(self)

    def __truediv__(self, other):
        return self.div(other, self.div_precision)

    def __rtruediv__(self, other):
        return BigDecimal(other).div(self)

    def __neg__(self):
        obj = BigDecimal(self)
        obj.sign = -obj.sign
        return obj

    def __abs__(self):
        obj = BigDecimal(self)
        obj.sign = 1
        return obj


def test():
    print("=" * 60)
    print("  无限位数计算器  ——  模拟小学竖式，支持任意精度小数")
    print("=" * 60)

    def show(title, expr, value):
        print(f"\n[{title}]")
        print(f"  {expr} = {value}")

    # # 加法
    # show("加法", "0.1 + 0.2", BigDecimal('0.1') + BigDecimal('0.2'))
    # show("加法", "123456789.987654321 + 987654321.123456789",
    #      BigDecimal('123456789.987654321') + BigDecimal('987654321.123456789'))
    # show("加法", "12345.6789 + 987.123456",
    #      BigDecimal('12345.6789') + BigDecimal('987.123456'))
    show("加法", "354.999999999999999999999999999956 + 0.000000000000000000000000000044",
         BigDecimal('354.999999999999999999999999999956') + BigDecimal('0.000000000000000000000000000044'))

    # # 减法
    # show("减法", "1 - 0.3", BigDecimal('1') - BigDecimal('0.3'))
    # show("减法", "0.3 - 1", BigDecimal('0.3') - BigDecimal('1'))
    # show("减法", "1000000000.0001 - 0.0001",
    #      BigDecimal('1000000000.0001') - BigDecimal('0.0001'))
    # show("减法", "-12345.6789 - 987.123456",
    #      BigDecimal('-12345.6789') - BigDecimal('987.123456'))

    # # 乘法
    # show("乘法", "0.1 * 0.1", BigDecimal('0.1') * BigDecimal('0.1'))
    # show("乘法", "12.34 * 56.78", BigDecimal('12.34') * BigDecimal('56.78'))
    # show("乘法", "123456789 * 987654321",
    #      BigDecimal('123456789') * BigDecimal('987654321'))
    show("乘法", "3.141592920353982300884955752212 * 113",
         BigDecimal('3.141592920353982300884955752212') * BigDecimal('113'))

    # # 除法
    # show("除法", "1 / 3 (保留30位)", BigDecimal('1').div(BigDecimal('3'), 30))
    # show("除法", "10 / 4", BigDecimal('10') / BigDecimal('4'))
    show("除法", "355 / 113 (保留30位, 圆周率近似)",
         BigDecimal('355').div(BigDecimal('113'), 30))
    # show("除法", "5.78 / 9.65 (保留20位)",
    #      BigDecimal('5.78').div(BigDecimal('9.65'), 20))
    # show("除法", "578.964 / 9.65 (保留20位)",
    #      BigDecimal('578.964').div(BigDecimal('9.65'), 9))
    # show("除法", "-578.964 / 9.65 (保留20位)",
    #      BigDecimal('-578.964').div(BigDecimal('9.65'), 6))

    print("\n" + "=" * 60)
    print("  对比：Python 原生浮点 0.1 + 0.2 =", 0.1 + 0.2)
    print("  本计算器        0.1 + 0.2 =", BigDecimal('0.1') + BigDecimal('0.2'))
    print("=" * 60)


if __name__ == '__main__':
    # test()
    gui = CalculatorGUI()
    gui._event_loop_()
