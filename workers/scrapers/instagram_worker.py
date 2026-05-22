# Wrapper para compatibilidade de importação
# Expondo a implementação real do worker de coleta Instagram

from .ig_zyte import IGZyteWorker as InstagramWorker
# Caso queira usar o headless como fallback, substitua a linha acima por:
# from .ig_headless import IGHeadlessWorker as InstagramWorker
