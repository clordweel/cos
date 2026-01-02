from .monkey_patches.currency_patch import apply_patch as apply_currency_patch
from .monkey_patches.company_tax_patch import apply_patch as apply_company_tax_patch

apply_currency_patch()
apply_company_tax_patch()
