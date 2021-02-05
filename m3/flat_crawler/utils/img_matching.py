import json
import logging
from abc import ABC, abstractmethod
from typing import NamedTuple, Tuple, Optional, Dict
from types import SimpleNamespace

import numpy as np
from PIL.Image import Image
from skimage import img_as_float
from skimage.metrics import structural_similarity

from flat_crawler.models import FlatPost, ImageMatch

logger = logging.getLogger(__name__)

COLOR_MAX = 255


class FlatPostImage(NamedTuple):
    flat_post: FlatPost
    image: Image
    # position of image on photos_bytes list
    img_pos: Optional[int] = None # none means it is thumbnail


class ImageData(SimpleNamespace):
    size: Optional[int] = None
    img_arr: Optional[np.array] = None
    img_arr_norm: Optional[np.array] = None
    img_as_float: Optional[np.array] = None
    img_arr_mean: Optional[np.array] = None
    img_arr_std: Optional[np.array] = None
    hist_norm: Optional[np.array] = None
    hist_std: Optional[float] = None



class BaseComparer(ABC):
    COMPARER_ID = None
    FIRST_THRESHOLD = None
    CONFIDENT_THRESHOLD = None

    @abstractmethod
    def get_match_score(img1: ImageData, img2: ImageData):
        pass

    @abstractmethod
    def add_image_data(img_data: ImageData, image: Image) -> ImageData:
        pass


class SimpleHistComparer(BaseComparer):
    COMPARER_ID = 'SimpleHistComparer'
    FIRST_THRESHOLD = 0.9
    CONFIDENT_THRESHOLD = 0.95
    DEFAULT_BINS = 20

    def __init__(self, bins=None, **kwargs):
        self._bins = bins or self.DEFAULT_BINS

    def _get_norm_hist(self, arr: np.array, c_ind: int) -> np.array:
        h = np.histogram(arr[..., c_ind], bins=self._bins, density=True, range=(0, 255))[0]
        return h / np.sum(h)

    def _get_hist(self, arr: np.array) -> np.array:
        return np.array([self._get_norm_hist(arr, i) for i in range(3)]).T

    def add_image_data(self, img_data: ImageData, image: Image) -> ImageData:
        if img_data.img_arr is None:
            img_data.img_arr = np.array(image.getdata())
        hist = self._get_hist(arr=img_data.img_arr)
        img_data.hist_norm = hist - np.mean(hist, axis=0)
        img_data.hist_std = np.std(hist, axis=0)
        return img_data

    def get_match_score(self, img1: ImageData, img2: ImageData) -> float:
        """ Computes cross correlation between image histograms. """
        denom = self._bins * img1.hist_std * img2.hist_std
        scores = np.sum(img1.hist_norm * img2.hist_norm, axis=0) / denom
        return min(scores)


class HistComparer(BaseComparer):
    COMPARER_ID = 'HistComparer'
    FIRST_THRESHOLD = 0.9
    CONFIDENT_THRESHOLD = 0.95

    def __init__(self, color_bins=6, **kwargs):
        self._cbins =  color_bins
        self._cbins2 =  color_bins ** 2
        self._cbins3 = color_bins ** 3
        self._bin_div = (COLOR_MAX / color_bins) + 0.0001
        self._hist_len = color_bins ** 3

    def _get_hist(self, image_arr: np.array) -> np.array:
        arr = (image_arr / self._bin_div).astype(int)
        col_arr = arr[..., 0] + arr[..., 1] * self._cbins + arr[..., 2] * self._cbins2
        return np.histogram(col_arr, bins=self._cbins3, range=(0, self._cbins3 - 1))[0]

    def add_image_data(self, img_data: ImageData, image: Image) -> ImageData:
        if img_data.img_arr is None:
            img_data.img_arr = np.array(image.getdata())
        hist = self._get_hist(image_arr=img_data.img_arr)
        img_data.hist_norm = hist / np.sum(hist)
        img_data.hist_std = np.std(img_data.hist_norm)
        return img_data

    def get_match_score(self, img1: ImageData, img2: ImageData) -> float:
        """ Computes cross correlation between image histograms. """
        # (hist length - 1) * std1 * std2
        denom = (self._cbins3 - 1) * img1.hist_std * img2.hist_std
        return np.sum(
            (img1.hist_norm - np.mean(img1.hist_norm)) * (img2.hist_norm - np.mean(img2.hist_norm))) / denom


class StructSimComparer(BaseComparer):
    COMPARER_ID = 'SsimComparer'
    FIRST_THRESHOLD = 0.6
    CONFIDENT_THRESHOLD = 0.9

    def add_image_data(self, img_data: ImageData, image: Image) -> ImageData:
        img_data.img_arr = np.array(image.getdata())
        if img_data.img_as_float is None:
            img_data.img_as_float = img_as_float(image)
        return img_data

    def get_match_score(self, img1: ImageData, img2: ImageData) -> float:
        try:
            return structural_similarity(img1.img_as_float, img2.img_as_float, multichannel=True)
        except ValueError as exc:
            logger.error(
                f"Error in SsimComparer:\n"
                f"\timg1_as_float.shape {img1.img_as_float.shape}\n"
                f"\timg2_as_float.shape {img2.img_as_float.shape}\n"
            )
            raise


class CrossCorrComparer(BaseComparer):
    COMPARER_ID = 'CrossCorrComparer'
    FIRST_THRESHOLD = 0.6
    CONFIDENT_THRESHOLD = 0.9

    def add_image_data(self, img_data: ImageData, image: Image) -> ImageData:
        if img_data.img_arr is None:
            img_data.img_arr = np.array(image.getdata())
        img_data.size = len(img_data.img_arr)
        img_data.img_arr_mean = np.mean(img_data.img_arr, axis=0)
        img_data.img_arr_std = np.std(img_data.img_arr, axis=0)
        return img_data

    def get_match_score(self, img1: ImageData, img2: ImageData) -> float:
        try:
            denom = (img1.size - 1) * img1.img_arr_std * img2.img_arr_std
            scores = np.sum((img1.img_arr - img1.img_arr_mean) * (img2.img_arr - img2.img_arr_mean), axis=0)
            return min(scores / denom)
        except ValueError as exc:
            logger.error(
                f"Error in CrossCorrComparer:\n"
                f"\timg1_arr_norm.shape {img1.img_arr_norm.shape}\n"
                f"\timg2_arr_norm.shape {img2.img_arr_norm.shape}\n"
            )
            raise


class ImageMatchingEngine(object):

    COMPARERS = [
        SimpleHistComparer,
        CrossCorrComparer,
        StructSimComparer,
    ]

    def __init__(self, stop_early: bool = False):
        self._comparers = [Comparer() for Comparer in self.COMPARERS]
        self._image_data_dict = dict()
        self._stop_early = stop_early

    @property
    def num_comparers(self) -> int:
        return len(self.COMPARERS)

    def get_image_match(
        self, fp_image_1: FlatPostImage, fp_image_2: FlatPostImage, dry: bool = False
    ) -> Optional[ImageMatch]:
        """ Get ImageMatch object for the given two FlatPostImage objects.
        Args:
            dry: If true, don't save ImageMatch objects.
        Returns: ImageMatch object if there's a match, None otherwise.
        """
        if self._imgs_not_comparable(fp_image_1.image, fp_image_2.image):
            return None
        if not dry:
            assert fp_image_1.flat_post != fp_image_2.flat_post, (
                "Don't try to compare images from the same flat. If you really want to do it, "
                "set dry=True (dry run doesn't save any objects"
            )

        # Keep order to avoid saving the same matching twice
        if fp_image_1.flat_post.id > fp_image_2.flat_post.id:
            fp_image_1, fp_image_2 = fp_image_2, fp_image_1

        image_match_q = ImageMatch.objects.filter(
            post_1=fp_image_1.flat_post,
            img_pos_1=fp_image_1.img_pos,
            post_2=fp_image_2.flat_post,
            img_pos_2=fp_image_2.img_pos,
        )
        assert len(image_match_q) <= 1, (
            f"Multiple ({len(image_match_q)}) ImageMatch objects for the same image pair: "
            f"{fp_image_1.flat_post}:{fp_image_1.img_pos}-{fp_image_2.flat_post}:{fp_image_2.img_pos}"
        )
        match = image_match_q.first()
        if match is None:
            try:
                match = self._get_image_match(fp_image_1, fp_image_2)
            except Exception as exc:
                logger.exception(
                    f"Exception while matching images:\n"
                    f"\t{fp_image_1.flat_post.id}:{fp_image_1.img_pos} - "
                    f"{fp_image_2.flat_post.id}:{fp_image_2.img_pos}"
                )
                raise
            if not dry and match is not None:
                match.save()
        return match

    def compare_images(self, img_1: Image, img_2: Image) -> Tuple[int, int, Dict]:
        """ Returns (num_maybe_matched, num_confirmed, details_dict) for pair of images. """
        if self._imgs_not_comparable(img_1, img_2):
            return 0, 0, {}
        img_data_1 = self._get_img_data_for_image(img_1)
        img_data_2 = self._get_img_data_for_image(img_2)
        return self._get_comparers_info(img_data_1, img_data_2)

    def _imgs_not_comparable(self, img_1: Image, img_2: Image) -> bool:
        if img_1.size != img_2.size:
            logger.warning(f"Image sizes differ. {img_1.size} vs {img_2.size}")
            return True
        if img_1.mode != 'RGB' or img_2.mode != 'RGB':
            return True
        return False

    def _get_img_data_for_image(self, img: Image) -> ImageData:
        img_data = ImageData()
        for comparer in self._comparers:
            img_data = comparer.add_image_data(img_data=img_data, image=img)
        return img_data

    def _get_img_data(self, fp_image: FlatPostImage):
        img_id = self._get_image_id(flat_post_id=fp_image.flat_post.id, img_pos=fp_image.img_pos)
        if not img_id in self._image_data_dict:
            self._image_data_dict[img_id] = self._get_img_data_for_image(img=fp_image.image)
        return self._image_data_dict[img_id]

    def _get_comparers_info(self, img_data_1: ImageData, img_data_2: ImageData):
        maybe_matched, confirmed = 0, 0
        details_dict = {}
        for comparer in self._comparers:
            match_score = comparer.get_match_score(img_data_1, img_data_2)
            if match_score >= comparer.CONFIDENT_THRESHOLD:
                confirmed += 1
            elif match_score >= comparer.FIRST_THRESHOLD:
                maybe_matched += 1
            elif self._stop_early:
                return 0, 0, {}
            details_dict[comparer.COMPARER_ID] = match_score
        return maybe_matched, confirmed, details_dict

    def _get_image_match(
        self, fp_image_1: FlatPostImage, fp_image_2: FlatPostImage
    ) -> Optional[ImageMatch]:
        img_data_1, img_data_2 = self._get_img_data(fp_image_1), self._get_img_data(fp_image_2)
        maybe_matched, confirmed, details_dict = self._get_comparers_info(img_data_1, img_data_2)

        # none of the comparers suggested match
        if maybe_matched + confirmed == 0:
            return None

        return ImageMatch(
            post_1=fp_image_1.flat_post,
            img_pos_1=fp_image_1.img_pos,
            post_2=fp_image_2.flat_post,
            img_pos_2=fp_image_2.img_pos,
            num_comparers_confirmed=confirmed,
            num_comparers_maybe_matched=maybe_matched,
            avg_score=np.average(list(details_dict.values())),
            details_json=json.dumps(details_dict),
        )

    def _get_image_id(self, flat_post_id: str, img_pos: Optional[int] = None) -> str:
        pos_str = str(img_pos) if img_pos else 'T'
        return f"{flat_post_id}:{pos_str}"
