ERC20_ABI = [
    {"constant": True, "inputs":[{"name":"owner","type":"address"}], "name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"type":"function"},
    {"constant": True, "inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}], "name":"allowance","outputs":[{"name":"","type":"uint256"}],"type":"function"},
    {"constant": False, "inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}], "name":"approve","outputs":[{"name":"","type":"bool"}],"type":"function"},
]

UNISWAP_V2_ROUTER_ABI = [
    {"name":"getAmountsOut","type":"function","stateMutability":"view",
     "inputs":[{"name":"amountIn","type":"uint256"},{"name":"path","type":"address[]"}],
     "outputs":[{"name":"amounts","type":"uint256[]"}]},
    {"name":"swapExactETHForTokens","type":"function","stateMutability":"payable",
     "inputs":[{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],
     "outputs":[{"name":"amounts","type":"uint256[]"}]},
    {"name":"swapExactTokensForETH","type":"function","stateMutability":"nonpayable",
     "inputs":[{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],
     "outputs":[{"name":"amounts","type":"uint256[]"}]},
    {"name":"swapExactTokensForTokens","type":"function","stateMutability":"nonpayable",
     "inputs":[{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}],
     "outputs":[{"name":"amounts","type":"uint256[]"}]},
]
