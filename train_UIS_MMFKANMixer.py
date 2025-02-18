import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
import time
import torch
import torchvision
from torch import nn, optim
from torch.utils import data
from torchvision import transforms
from dataloader_UIS import Mydataset
import argparse

from models.model_fuse_KAN import MMFKANMixerUV,MMFKANMixerUV_resnet
import torchvision.models as models

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')



class FCViewer(nn.Module):
    def forward(self, x):
        return x.view(x.size(0), -1)

def main(args):
    if not os.path.exists(args.model_path):
        os.makedirs(args.model_path)


    train_txt='data\\train_7_3_0.txt'
    val_txt='data\\test_7_3_0.txt'
    test_txt='data\\test_7_3_0.txt'


    transform_rs = torchvision.transforms.Compose([torchvision.transforms.ToTensor()])
    transform_sv = torchvision.transforms.Compose([torchvision.transforms.Resize((224,224)),
                                                 torchvision.transforms.ToTensor()])


    train_dataset=Mydataset(txt=train_txt, transform_rs=transform_rs, transform_sv=transform_sv)
    val_dataset=Mydataset(txt=val_txt, transform_rs=transform_rs, transform_sv=transform_sv)
    test_dataset=Mydataset(txt=test_txt, transform_rs=transform_rs, transform_sv=transform_sv)

    train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, pin_memory=True)
    val_loader=torch.utils.data.DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, pin_memory=True)
    test_loader = torch.utils.data.DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False, pin_memory=True)

    print("Train numbers:{:d}".format(len(train_dataset)))
    print("Val numbers:{:d}".format(len(val_dataset)))
    print("Test numbers:{:d}".format(len(test_dataset)))

    model2 = MMFKANMixerUV(2)

    print('model2 parameters:', sum(p.numel() for p in model2.parameters() if p.requires_grad))
    # print('model3 parameters:', sum(p.numel() for p in model3.parameters() if p.requires_grad))

    # model1 = model1.to(device)
    model2 = model2.to(device)
    # model3 = model3.to(device)
    # cost1 = nn.CrossEntropyLoss().to(device)
    cost2 = nn.CrossEntropyLoss().to(device)
    # cost2 = CB_loss(0.9999, 2.0).to(device)
    # cost3 = nn.CrossEntropyLoss().to(device)
    # Optimization
    # optimizer1 = optim.Adam(model1.parameters(), lr=args.lr, weight_decay=1e-6)
    optimizer2 = optim.Adam(model2.parameters(), lr=args.lr, weight_decay=1e-6)
    # optimizer2 = torch.optim.SGD(model2.parameters(), lr=args.lr, momentum=0.9)
    # scheduler2 = torch.optim.lr_scheduler.OneCycleLR(optimizer2,max_lr=0.9,total_steps=100, verbose=False)
    # scheduler2 = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer2, mode='min', factor=0.9, patience=4, verbose=False, threshold=0.0001, threshold_mode='rel', cooldown=0, min_lr=0.000001, eps=1e-08)
    # criterion=nn.CrossEntropyLoss()
    # optimizer3 = optim.Adam(model3.parameters(), lr=args.lr, weight_decay=1e-6)



    best_acc_2 = 0.
    best_epoch = 0
    classes = ('UIS', 'not-UIS')

    for epoch in range(1, args.epochs + 1):
        # model1.train()
        model2.train()
        # model3.train()
        # start time
        start = time.time()
        index = 0
        for images, sv0, sv1, sv2, sv3, labels in train_loader:
            images = images.to(device)
            # print(images.shape)
            labels = labels.to(device)
            sv0 = sv0.to(device)
            sv1 = sv1.to(device)
            sv2 = sv2.to(device)
            sv3 = sv3.to(device)

            # checkin = checkin.to(device)
            # checkin = checkin.clone().detach().float()


            # Forward pass
            # outputs1 = model1(images)
            img_feature, outputs2 = model2(images, sv0, sv1, sv2, sv3)
            # outputs3 = model3(images)
            # loss1 = cost1(outputs1, labels)
            loss2 = cost2(outputs2, labels)
            # loss3 = cost3(outputs3, labels)

            # if index % 10 == 0:
                # print (loss)
            # Backward and optimize
            # optimizer1.zero_grad()
            optimizer2.zero_grad()
            # optimizer3.zero_grad()
            # loss1.backward()
            loss2.backward()
            # loss3.backward()
            # optimizer1.step()
            optimizer2.step()
            # scheduler2.step(loss2)
            # optimizer3.step()
            index += 1


        if epoch % 1 == 0:
            model2.eval()
            class_correct2 = list(0. for i in range(args.num_class))
            class_total2 = list(0. for i in range(args.num_class))
            correct_prediction_2 = 0.
            total_2 = 0
            with torch.no_grad():
                for images, sv0, sv1, sv2, sv3, labels in val_loader:
                    images = images.to(device)
                    # print(images.shape)
                    labels = labels.to(device)
                    sv0 = sv0.to(device)
                    sv1 = sv1.to(device)
                    sv2 = sv2.to(device)
                    sv3 = sv3.to(device)

                    # checkin = checkin.to(device)
                    # checkin = checkin.clone().detach().float()


                    # Forward pass
                    # outputs1 = model1(images)
                    img_feature, outputs2 = model2(images, sv0, sv1, sv2, sv3)

                    _2, predicted2 = torch.max(outputs2, 1)
                    c2 = (predicted2 == labels).squeeze()
                    # print(len(labels))
                    for label_idx in range(len(labels)):
                        # print(label_idx)
                        label = labels[label_idx]
                        # print(label)
                        class_correct2[label] += c2[label_idx].item()
                        class_total2[label] += 1
                    total_2 += labels.size(0)
                    # add correct
                    correct_prediction_2 += (predicted2 == labels).sum().item()

            end = time.time()
            print("Epoch [%d/%d], Loss: %.8f, Time: %.1fsec!" % (epoch, args.epochs, loss2.item(), (end-start)))

            for i in range(args.num_class):
                print('Model MMFKANMixer - Accuracy of %5s : %2d %%: Correct Num: %d in Total Num: %d' % (
                    classes[i], 100 * class_correct2[i] / class_total2[i], class_correct2[i], class_total2[i]))
            acc_2 = correct_prediction_2 / total_2
            print("Total Acc Model: %.4f" % (correct_prediction_2 / total_2))

            if acc_2 > best_acc_2:
                print('save new best acc', acc_2)
                torch.save(model2, os.path.join(args.model_path, 'ChinaUIS\\MMFKANMixer-UIS_batch_16_5.pth'))
                best_acc_2 = acc_2
                best_epoch = epoch

            print(f"best acc : {best_acc_2}\t best epoch : {best_epoch}")
            print('----------------------------------------------------')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='train hyper-parameter')
    parser.add_argument("--num_class", default=2, type=int)
    parser.add_argument("--epochs", default=200, type=int)
    # parser.add_argument("--net", default='ResNet50', type=str)
    # parser.add_argument("--depth", default=50, type=int)
    parser.add_argument("--lr", default=1e-5, type=float)
    parser.add_argument("--batch_size", default=16, type=int)
    # parser.add_argument("--num_workers", default=2, type=int)
    parser.add_argument("--model_name", default='', type=str)
    parser.add_argument("--model_path", default='./model-UIS', type=str)
    parser.add_argument("--pretrained", default=False, type=bool)
    parser.add_argument("--pretrained_model", default='', type=str)
    args = parser.parse_args()

    main(args)
