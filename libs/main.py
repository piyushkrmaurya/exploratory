from beta_coreference import *

sentences = "Sarah, is a judge at the beautiful Florida Court. She usually checks our classroom on Fridays. the Florida Court is often empty and we are ready with the Florida Court cleaned and well groomed."

cr = CoreferenceResolution(sentences)
cr.resolve()
