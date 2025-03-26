from similar_images.google_playwright import extract_image_urls_from_js
from playwright.async_api import async_playwright
import pytest
from pathlib import Path

expected = {
    "tests/data/bigcats.html": [
        "https://wildlife.forestry.ubc.ca/files/2018/03/big-cats-4s.jpg",
        "https://i.natgeofe.com/n/928a0711-d14f-46b4-b1c9-75a0ef14b54b/big-cats-thumbnail_02.jpg",
        "https://i.natgeofe.com/n/2b4c9c79-c7a2-4c42-8256-c1fdc3ef654d/big-cats_03.jpg?wp\\u003d1\\u0026w\\u003d1084.125\\u0026h\\u003d721.875",
        "https://d1jyxxz9imt9yb.cloudfront.net/medialib/1947/image/s768x1300/leopard-PaulaDurbin-Botswana.jpg",
        "https://image.petmd.com/files/inline-images/big-cat-breeds-savannah-cat.jpg?VersionId\\u003dmgl9kEVzhYRxzjMS2YRnuuelb12l.f2a",
        "https://upload.wikimedia.org/wikipedia/commons/c/cd/4panthera3.0.png",
        "https://c02.purpledshub.com/uploads/sites/62/2014/09/GettyImages-1018211394-68c8ee6.jpg?webp\\u003d1\\u0026w\\u003d1200",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/Caracal_on_the_road%2C_early_morning_in_Kgalagadi_%2836173878220%29_%28cropped%29.jpg/640px-Caracal_on_the_road%2C_early_morning_in_Kgalagadi_%2836173878220%29_%28cropped%29.jpg",
        "https://cdn.kpbs.org/8b/04/f40470a744aa888b04190b0b4e52/big-cats-24-7-first-look.jpg",
        "https://panthera.org/sites/default/files/blog-post-images/ZAF_BWA_181018_1628_12340_F.jpg",
        "https://dinoanimals.com/wp-content/uploads/2016/06/Largest-wild-cats-1120x700.jpg",
        "https://bigcatswildcats.com/wp-content/uploads/2022/05/Big-Cats-Cheetah.jpg",
        "https://www.usatoday.com/gcdn/media/2022/04/05/USATODAY/usatsports/imageForEntry9-eZm.jpg",
        "https://blog.nature.org/wp-content/uploads/2022/05/29473548577_8414ac0a6e_k.jpg",
        "https://images.theconversation.com/files/543214/original/file-20230817-24-1bzl9.jpg?ixlib\\u003drb-4.1.0\\u0026rect\\u003d17%2C40%2C2977%2C1953\\u0026q\\u003d20\\u0026auto\\u003dformat\\u0026w\\u003d320\\u0026fit\\u003dclip\\u0026dpr\\u003d2\\u0026usm\\u003d12\\u0026cs\\u003dstrip",
        "https://d18x2uyjeekruj.cloudfront.net/wp-content/uploads/2022/09/panthera-300x271.jpg",
        "https://nystateparks.blog/wp-content/uploads/2019/02/bobcatterry-spivey-usda-forest-service-bugwood.org_.jpg",
        "https://www.travel4wildlife.com/wp-content/uploads/2018/05/the-biggest-cats-in-the-world.jpg",
        "https://media.istockphoto.com/id/1209624728/vector/big-cats-bundle-set.jpg?s\\u003d612x612\\u0026w\\u003d0\\u0026k\\u003d20\\u0026c\\u003dOfIhZCbk0VECnhtvWbytZIpswrhA0KeK4V5HZFtH5tE\\u003d",
        "https://bigcatswildcats.com/wp-content/uploads/2019/01/tiger-big-cat-facts.jpg",
        "https://i.natgeofe.com/n/c928f1fc-8181-42ca-bcee-3da31a894493/big-cats_12.jpg?wp\\u003d1\\u0026w\\u003d1084.125\\u0026h\\u003d721.875",
        "https://d1jyxxz9imt9yb.cloudfront.net/medialib/3910/image/s768x1300/LC202306_AmboseliWildlife_049_429159_reduced.jpg",
        "https://cnr.ncsu.edu/news/wp-content/uploads/sites/10/2019/07/07182019-leopard-tree-unsplash-featured.jpg",
        "https://www.activewild.com/wp-content/uploads/2020/06/Types-Of-Wild-Cats.jpg",
        "https://publish.purewow.net/wp-content/uploads/sites/2/2021/07/large-cat-breeds-norwegian-forest.jpg?fit\\u003d728%2C524",
        "https://hips.hearstapps.com/hmg-prod/images/large-cat-breed-1553197454.jpg",
        "https://www.fourpaws.com/-/media/Project/OneWeb/FourPaws/Images/articles/cat-corner/large-cat-breeds/maine-coon-cat-cropped.jpg",
        "https://www.rover.com/blog/wp-content/uploads/2019/07/savannah-cat-518134_640.jpg",
        "https://paradepets.com/.image/w_3840,q_auto:good,c_fill,ar_4:3/MTkxMzY1Nzg4OTYxMjIwMTI5/20-big-cat-breeds-1-jpg.jpg",
        "https://images.litter-robot.com/media/magefan_blog/2021/09/maine-coon-1.jpeg",
        "https://image.petmd.com/files/inline-images/big-cat-breed-norwegian-forest-cat.jpg?VersionId\\u003drFp0NWXhlbmmwfoSWcC7aQ2x0PFQ9DFP",
        "https://wwf.ca/wp-content/uploads/2021/10/shutterstock_1278411223-c-stefbennett-scaled.jpg",
        "https://images.squarespace-cdn.com/content/v1/583eea74be659429d12fb2a8/1480706123921-9XGQF8YX2T1LEE6J4G9I/GU98248.jpg",
        "https://columbiametro.com/wp-content/uploads/2020/10/iStock-682944364-scaled.jpg",
        "https://image.petmd.com/files/styles/978x550/public/2024-12/big-cat-breeds.jpg",
        "https://toymany.com/cdn/shop/articles/Exploring_the_World_of_Wildlife_Big_Cats.png?v\\u003d1724384749\\u0026width\\u003d1500",
        "https://cdn.britannica.com/03/190303-131-EEAE3396/puma-mountain-lion-cougar-panther.jpg",
        "https://static.euronews.com/articles/stories/05/34/39/60/1440x810_cmsv2_b22bbaea-d6a6-5aa0-9084-94b6243e6a24-5343960.jpg",
        "https://ichef.bbci.co.uk/ace/standard/624/cpsprodpb/B9AE/production/_99643574_14905719-low_res-big-cats.jpg",
        "https://www.thewildlifediaries.com/wp-content/uploads/2018/12/All-types-of-wild-cats.jpg",
        "https://image.petmd.com/files/inline-images/big-cat-breeds-american-bobtail.jpg?VersionId\\u003d_hx0QyOw81cp_7O9uxuOdw_7QD0Lompp",
        "https://cites.org/sites/default/files/inline-images/BCTF%202023%20banner_0.jpg",
        "https://antinol.co.uk/cdn/shop/files/Neron_1500x.jpg?v\\u003d1718614697",
        "https://i.ytimg.com/vi/7HZiID6jGgU/maxresdefault.jpg",
        "https://cattyshack.org/wp-content/uploads/2018/02/florida_panther_family_5164634982.jpg",
        "https://images.newscientist.com/wp-content/uploads/2020/01/08132946/1200x800-h_03967873.jpg",
        "https://africageographic.com/wp-content/uploads/2018/04/Keith-Bannerman-Lion-Cubs-Dinaka-Central-Kalahar-Game-Reserve-Botswana-cover-1920.jpg",
        "https://www.usatoday.com/gcdn/-mm-/803c15bd273d372875b2841d61836c1f8f5986b5/c\\u003d0-116-3547-2120/local/-/media/2017/12/05/USATODAY/USATODAY/636480790078987808-AFP-AFP-TA5JE.jpg?width\\u003d3200\\u0026height\\u003d1808\\u0026fit\\u003dcrop\\u0026format\\u003dpjpg\\u0026auto\\u003dwebp",
        "https://i.ytimg.com/vi/1fA_Nbb4xz4/hq720.jpg?sqp\\u003d-oaymwEhCK4FEIIDSFryq4qpAxMIARUAAAAAGAElAADIQj0AgKJD\\u0026rs\\u003dAOn4CLDOCdM73VJbXMTpP6kHKxblYWcJxQ",
        "https://media.4-paws.org/e/2/c/8/e2c8248def2b8843955ab43c691eb39a1292075c/VP0154004.jpg",
        "https://alabamanewscenter.com/wp-content/uploads/2023/08/Mountain-lion-alabama-extension.jpg",
        "https://media.posterlounge.com/img/products/770000/769161/769161_poster.jpg",
        "https://i.natgeofe.com/n/6a40a07d-501d-4b71-be5e-89f5a0ed952e/03bigcatgallery.jpg",
        "https://www.nps.gov/features/bicy/climatechange/BICY708/img/gallery/3.jpg",
        "https://www.earthreminder.com/wp-content/uploads/2023/03/types-of-wild-cats-1.jpg",
        "https://panthera.org/sites/default/files/blog-post-images/_DCS1015.jpeg",
        "https://m.media-amazon.com/images/I/51N2FGB9G4L._AC_UF1000,1000_QL80_.jpg",
        "https://i.etsystatic.com/10291239/r/il/35787d/3397582918/il_1080xN.3397582918_g6d7.jpg",
        "https://panthera.org/sites/default/files/blog-post-images/2019_Blog_MelanisticCatGrid%20%281%29.jpeg",
        "https://m.media-amazon.com/images/I/91kOyzVRaTL.jpg",
        "https://www.treehugger.com/thmb/GYoUKBWnDGOUW-PAAfIj58z4WWA\\u003d/1500x0/filters:no_upscale():max_bytes(150000):strip_icc()/GettyImages-640977760-1a7d3046eb514b3a975d497407568151.jpg",
        "https://media.4-paws.org/6/6/2/c/662c2a475c3e6bc3842bae1f37a74e58968b02a5/VIER%20PFOTEN_2018-09-14_054-1927x1333-1920x1328.jpg",
        "https://www.nps.gov/features/bicy/climatechange/BICY708/img/gallery/1.jpg",
        "https://th-thumbnailer.cdn-si-edu.com/IpjPOuyCDuFKV6C86HhcBC9d_YM\\u003d/800x800/https://tf-cmsv2-smithsonianmag-media.s3.amazonaws.com/filer/6a/fa/6afa4efa-3f5a-4ea7-90ea-e47173217d59/42-29316901.jpg",
        "https://images.newscientist.com/wp-content/uploads/2023/08/16100818/SEI_167697517.jpg",
        "https://m.media-amazon.com/images/I/71gbfUcCn-L._AC_UF894,1000_QL80_.jpg",
        "https://ohiowildlifecenter.org/wp-content/uploads/2021/03/bobcat-by-Tim-Daniel-ODNR-3.21-banner.jpg",
        "https://i.pinimg.com/736x/9e/b2/75/9eb27556ed308b5ebf5f1e8803f30088.jpg",
        "https://images.squarespace-cdn.com/content/v1/66ec3b49803ab81bf84f89e4/1737487592842-KEDEP8489GIR48NABDLK/Rambo-JungleCat-2025.jpg",
        "https://wildcatconservation.org/wp-content/uploads/2012/12/400px-Canada_lynx_by_Michael_Zahra.jpg",
        "https://transforms.stlzoo.org/production/site/leopard_meibaum_220210_51284.jpg?w\\u003d2100\\u0026h\\u003d2482\\u0026auto\\u003dcompress%2Cformat\\u0026fit\\u003dcrop\\u0026dm\\u003d1664565315\\u0026s\\u003d1a61bc933cf20a361e13d57632cf9e02",
        "https://www.fourpaws.com/-/media/Project/OneWeb/FourPaws/Images/articles/cat-corner/large-cat-breeds/bengal-cat.jpg",
        "https://breed-assets.wisdompanel.com/cat/big-cats/Jaguar.png",
        "https://www.mosaicpuzzles.co/cdn/shop/products/Big-Cats-1280-_cut.jpg?v\\u003d1655735678",
        "https://c02.purpledshub.com/uploads/sites/62/2023/05/GettyImages-1390825179-2c3574e.jpg",
        "https://images.theconversation.com/files/192832/original/file-20171101-19876-1hctdqe.jpg?ixlib\\u003drb-4.1.0\\u0026q\\u003d45\\u0026auto\\u003dformat\\u0026w\\u003d926\\u0026fit\\u003dclip",
        "https://blog.nature.org/wp-content/uploads/2022/05/Flat-headed_cat_1_Jim_Sanderson_2.jpg",
        "https://cats.com/wp-content/uploads/2022/08/baby-caracal-cats-compressed.jpg",
        "https://cdn1.matadornetwork.com/blogs/1/2018/04/shutterstock_474609328.jpg",
        "https://www.wildcatfamily.com/wp-content/uploads/2021/07/2020-Castello-Felids-and-Hyenas-of-the-World.jpg",
        "https://th-thumbnailer.cdn-si-edu.com/nhLW4xtiq4JnPwIsWMqRsGTUZ2Y\\u003d/800x0/filters:no_upscale()/https://tf-cmsv2-smithsonianmag-media.s3.amazonaws.com/filer/38/a2/38a25041-ce7f-464b-a2fb-4ca61cbfbde5/ab006594.jpg",
        "https://wildcatconservation.org/wp-content/uploads/2012/12/570px-Asian_Golden_cat50.jpg",
        "https://www.thewildlifediaries.com/wp-content/uploads/2018/11/Snapseed-1-1024x683.jpg",
        "https://www.pbs.org/wnet/nature/files/2008/10/ChasingBigCats-SpeciesGuide.jpg",
        "https://m.media-amazon.com/images/I/81o-86pdj3L.jpg",
        "https://storage.googleapis.com/chile-travel-cdn/2021/08/pumas-sarabia_ok-2.jpg",
        "https://bigcatswildcats.com/wp-content/uploads/2022/05/big-cats-the-facts.jpg",
        "https://www.lionstigersandbears.org/wp-content/uploads/2024/11/Denali-Serval-Cat-at-Lions-Tigers-and-Bears-San-Diego-CA-950x1024.jpg",
        "https://images.photowall.com/products/57453/big-cats-of-the-world.jpg?h\\u003d699\\u0026q\\u003d85",
        "https://m.media-amazon.com/images/M/MV5BN2YxNTU3M2UtODhkOC00MDViLWI4OTItNzRiOWNhODlmYmNkXkEyXkFqcGc@._V1_.jpg",
        "https://bigcathabitat.org/wp-content/uploads/2023/03/A4111660-CBEF-4776-98D3-C04809B4FEC5.jpg",
        "https://uchytel.com/image/cache/catalog/size/The-Central-and-South-American-Big-cats-(Pleistocene)-414x331.jpg",
        "https://wolfcenter.org/wp-content/uploads/2022/09/unnamed-8.jpg",
        "https://media.4-paws.org/d/2/0/f/d20f54cb61a264106844fcd8b6a6c62d7bbcef95/VIER%20PFOTEN_2016-01-28_007.jpg",
        "https://images.squarespace-cdn.com/content/v1/66ec3b49803ab81bf84f89e4/1726788153507-YAZRK2A3KRGHEXMGSOEV/JoJo2012BigHiss.jpg",
    ],
}


@pytest.mark.parametrize(
    "path",
    [
        "tests/data/bigcats.html",
    ],
)
@pytest.mark.asyncio
async def test_big_cats(path):
    async with async_playwright() as p:
        # GIVEN
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(f"file://{Path(path).absolute()}")
        # WHEN
        links = await extract_image_urls_from_js(page)
        # THEN
        assert links == expected[path]
