#! /usr/bin/env python
# -*- coding: utf-8 -*-#

import json
from xmltodict import parse


def xml_file_to_json_file(xml_file, json_file):
    with open(xml_file, mode="r") as f, open(json_file, "w") as f1:
        order_dict = parse(f.read(), encoding="utf-8")
        common_dict = json.loads(json.dumps(order_dict, ensure_ascii=False))
        json_str = json.dumps(common_dict)
        f1.write(json_str)
        return common_dict


def xml_data_to_json_data(xml_data):
    """将xml格式数据转为json格式数据
    返回值为python字典格式
    """
    order_dict = parse(xml_data, encoding="utf-8")
    return json.loads(json.dumps(order_dict, ensure_ascii=False))


if __name__ == '__main__':
    xml_file_to_json_file("result.xml", "result.json")