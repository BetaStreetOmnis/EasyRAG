from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
import numpy as np


# embedding model
model_id = "iic/nlp_gte_sentence-embedding_chinese-base"
pipeline_se = pipeline(Tasks.sentence_embedding,
                       model=model_id,
                       sequence_length=512
                       ) 

def get_embedding(text):
    print(text)
    inputs = {
        "source_sentence": [text]
    }
    result = pipeline_se(input=inputs)
    text = result['text_embedding'][0]
    vector = np.array(text, dtype=np.float32)
    vector = (vector / np.linalg.norm(vector))[:512]
    return vector.tolist()




