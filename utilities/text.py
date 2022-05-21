import re

hashtag_fix_pattern = re.compile('[#]{2}')
hashtag_finder_pattern = re.compile(r"(?:^|\s)[＃#](\w+)", re.UNICODE)
mention_fix_pattern = re.compile('[@]{2}')
mention_finder_pattern = re.compile(r"(?:^|\s)[＠ @]([^\s#<>[\]|{}]+)", re.UNICODE)


def hashtag_extractor(raw_body):
    hashtags = re.findall(pattern=hashtag_finder_pattern,
                          string=re.sub(pattern=hashtag_fix_pattern, repl='', string=raw_body))

    return set(hashtags)


def mention_extractor(raw_body):
    mentions = re.findall(pattern=mention_finder_pattern,
                          string=re.sub(pattern=mention_fix_pattern, repl='', string=raw_body))

    return set(mentions)
