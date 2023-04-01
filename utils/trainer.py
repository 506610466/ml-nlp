import torch.nn as nn
import torch
from sklearn.model_selection import StratifiedKFold, KFold
import transformers
from tqdm import tqdm
transformers.logging.set_verbosity_error()


class Train(object):
    def __init__(self, model: nn.Module, epochs=20, lr=1e-5, weight_decay=0, 
                 show_batch=50, use_cuda=True,compute_metrics=None):
        self.model = model
        self.device = torch.device(
            "cuda:0" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.epochs = epochs
        self.lr = lr
        self.show_batch = show_batch
        self.weight_decay = weight_decay
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(), lr=self.lr, weight_decay=self.weight_decay)
        self.compute_metrics = compute_metrics
    def train(self, dataset_train, dataset_eval=None):
        for epoch in range(self.epochs):
            self.model.train()
            for idx, batch in tqdm(enumerate(dataset_train), total=len(dataset_train)):
                batch = {k: v.to(self.device) for k, v in batch.items()}
                score = self.compute_metrics(batch)
                loss = self.model(**batch)["loss"]
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()
                if idx % self.show_batch == 0:
                    print(
                        'Epoch [{}/{}],batch:{} Loss: {:.4f}'.format(self.epochs, epoch + 1, idx, loss.item()))
            with torch.no_grad():  # 评估时禁止计算梯度
                self.evaluation(dataset_eval, epoch)

    def evaluation(self, dataset_eval, epoch):
        print("evaluation.....")
        self.model.eval()
        score_list = []
        for idx, batch in tqdm(enumerate(dataset_eval), total=len(dataset_eval)):
            batch = {k: v.to(self.device) for k, v in batch.items()}
            score = self.compute_metrics(batch)
            score_list.append(score)
        score = sum(score_list) / len(score_list) * 100
        print(
            'Epoch [{}/{}], score: {:.4f} %'.format(self.epochs, epoch + 1, score))
   