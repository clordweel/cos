import frappe.utils
import frappe.utils.data


# 1. 备份系统原生的 money_in_words 函数
# 我们需要保留它，以便处理非 CNY 的货币（如 USD）
_original_money_in_words = frappe.utils.money_in_words


# 2. 定义拦截函数
def money_in_words_patched(number, main_currency=None, fraction_currency=None):
    from ..utils.currency import get_rmb_upper

    """
    全局劫持 money_in_words
    如果是 CNY，调用自定义 cn2an 逻辑；
    如果是其他货币，放行给原生逻辑。
    """
    if main_currency == "CNY":
        try:
            # 直接调用你在 utils.py 里写的成熟函数
            return get_rmb_upper(number)
        except Exception as e:
            # 容错机制：万一转换出错，记录日志并回退到原生逻辑，防止系统崩溃
            print(f"CNY Conversion Failed: {e}")
            pass

    # 非 CNY 货币，或转换出错时，原样调用系统原生函数
    return _original_money_in_words(number, main_currency, fraction_currency)


def apply_patch():
    # 3. 实施“热替换” (Monkey Patch)
    # 这里有两处引用需要替换，以防万一
    frappe.utils.money_in_words = money_in_words_patched
    frappe.utils.data.money_in_words = money_in_words_patched
