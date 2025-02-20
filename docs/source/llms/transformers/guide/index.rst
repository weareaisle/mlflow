🤗 Transformers within MLflow
=============================

.. attention::
    The ``transformers`` flavor is in active development and is marked as Experimental. Public APIs may change and new features are
    subject to be added as additional functionality is brought to the flavor.

The ``transformers`` model flavor enables logging of
`transformers models, components, and pipelines <https://huggingface.co/docs/transformers/index>`_ in MLflow format via
the :py:func:`mlflow.transformers.save_model()` and :py:func:`mlflow.transformers.log_model()` functions. Use of these
functions also adds the ``python_function`` flavor to the MLflow Models that they produce, allowing the model to be
interpreted as a generic Python function for inference via :py:func:`mlflow.pyfunc.load_model()`.
You can also use the :py:func:`mlflow.transformers.load_model()` function to load a saved or logged MLflow
Model with the ``transformers`` flavor in the native transformers formats.

Input and Output types for PyFunc
---------------------------------

The ``transformers`` :ref:`python_function (pyfunc) model flavor <pyfunc-model-flavor>` simplifies
and standardizes both the inputs and outputs of pipeline inference. This conformity allows for serving
and batch inference by coercing the data structures that are required for ``transformers`` inference pipelines
to formats that are compatible with json serialization and casting to Pandas DataFrames.

.. note::
    Certain `TextGenerationPipeline` types, particularly instructional-based ones, may return the original
    prompt and included line-formatting carriage returns `"\n"` in their outputs. For these pipeline types,
    if you would like to disable the prompt return, you can set the following in the `model_config` dictionary when
    saving or logging the model: `"include_prompt": False`. To remove the newline characters from within the body
    of the generated text output, you can add the `"collapse_whitespace": True` option to the `model_config` dictionary.
    If the pipeline type being saved does not inherit from `TextGenerationPipeline`, these options will not perform
    any modification to the output returned from pipeline inference.

.. attention::
    Not all ``transformers`` pipeline types are supported. See the table below for the list of currently supported Pipeline
    types that can be loaded as ``pyfunc``.

    In the current version, audio and text-based large language
    models are supported for use with ``pyfunc``, while computer vision, multi-modal, timeseries,
    reinforcement learning, and graph models are only supported for native type loading via :py:func:`mlflow.transformers.load_model()`

    Future releases of MLflow will introduce ``pyfunc`` support for these additional types.

The table below shows the mapping of ``transformers`` pipeline types to the :ref:`python_function (pyfunc) model flavor <pyfunc-model-flavor>`
data type inputs and outputs.

.. important::
    The inputs and outputs of the ``pyfunc`` implementation of these pipelines *are not guaranteed to match* the input types and output types that would
    return from a native use of a given pipeline type. If your use case requires access to scores, top_k results, or other additional references within
    the output from a pipeline inference call, please use the native implementation by loading via :py:func:`mlflow.transformers.load_model()` to
    receive the full output.

    Similarly, if your use case requires the use of raw tensor outputs or processing of outputs through an external ``processor`` module, load the
    model components directly as a ``dict`` by calling :py:func:`mlflow.transformers.load_model()` and specify the ``return_type`` argument as 'components'.

Supported transformers Pipeline types for Pyfunc
------------------------------------------------

================================= ============================== ==========================================================================
Pipeline Type                     Input Type                     Output Type
================================= ============================== ==========================================================================
Instructional Text Generation     str or List[str]               List[str]
Conversational                    str or List[str]               List[str]
Summarization                     str or List[str]               List[str]
Text Classification               str or List[str]               pd.DataFrame (dtypes: {'label': str, 'score': double})
Text Generation                   str or List[str]               List[str]
Text2Text Generation              str or List[str]               List[str]
Token Classification              str or List[str]               List[str]
Translation                       str or List[str]               List[str]
ZeroShot Classification*          Dict[str, [List[str] | str]*   pd.DataFrame (dtypes: {'sequence': str, 'labels': str, 'scores': double})
Table Question Answering**        Dict[str, [List[str] | str]**  List[str]
Question Answering***             Dict[str, str]***              List[str]
Fill Mask****                     str or List[str]****           List[str]
Feature Extraction                str or List[str]               np.ndarray
AutomaticSpeechRecognition        bytes*****, str, or np.ndarray List[str]
AudioClassification               bytes*****, str, or np.ndarray pd.DataFrame (dtypes: {'label': str, 'score': double})
================================= ============================== ==========================================================================

\* A collection of these inputs can also be passed. The standard required key names are 'sequences' and 'candidate_labels', but these may vary.
Check the input requirments for the architecture that you're using to ensure that the correct dictionary key names are provided.

\** A collection of these inputs can also be passed. The reference table must be a json encoded dict (i.e. {'query': 'what did we sell most of?', 'table': json.dumps(table_as_dict)})

\*** A collection of these inputs can also be passed. The standard required key names are 'question' and 'context'. Verify the expected input key names match the
expected input to the model to ensure your inference request can be read properly.

\**** The mask syntax for the model that you've chosen is going to be specific to that model's implementation. Some are '[MASK]', while others are '<mask>'. Verify the expected syntax to
avoid failed inference requests.

\***** If using `pyfunc` in MLflow Model Serving for realtime inference, the raw audio in bytes format must be base64 encoded prior to submitting to the endpoint. String inputs will be interpreted as uri locations.

Using model_config and model signature params for `transformers` inference
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For `transformers` inference, there are two ways to pass in additional arguments to the pipeline.

* Use ``model_config`` when saving/logging the model. Optionally, specify ``model_config`` when calling ``load_model``.
* Specify params at inference time when calling ``predict()``

Use ``model_config`` to control how the model is loaded and inference performed for all input samples. Configuration in
``model_config`` is not overridable at ``predict()`` time unless a ``ModelSignature`` is indicated with the same parameters.

Use ``ModelSignature`` with params schema, on the other hand, to allow downstream consumers to provide additional inference
params that may be needed to compute the predictions for their specific samples.

.. note::
    If both ``model_config`` and ``ModelSignature`` with parameters are saved when logging model, both of them
    will be used for inference. The default parameters in ``ModelSignature`` will override the params in ``model_config``.
    If extra ``params`` are provided at inference time, they take precedence over all params. We recommend using 
    ``model_config`` for those parameters needed to run the model in general for all the samples. Then, add 
    ``ModelSignature`` with parameters for those extra parameters that you want downstream consumers to indicated at
    per each of the samples.

* Using ``model_config``

.. code-block:: python

    import mlflow
    from mlflow.models import infer_signature
    from mlflow.transformers import generate_signature_output
    import transformers

    architecture = "mrm8488/t5-base-finetuned-common_gen"
    model = transformers.pipeline(
        task="text2text-generation",
        tokenizer=transformers.T5TokenizerFast.from_pretrained(architecture),
        model=transformers.T5ForConditionalGeneration.from_pretrained(architecture),
    )
    data = "pencil draw paper"

    # Infer the signature
    signature = infer_signature(
        data,
        generate_signature_output(model, data),
    )

    # Define an model_config
    model_config = {
        "num_beams": 5,
        "max_length": 30,
        "do_sample": True,
        "remove_invalid_values": True,
    }

    # Saving model_config with the model
    mlflow.transformers.save_model(
        model,
        path="text2text",
        model_config=model_config,
        signature=signature,
    )

    pyfunc_loaded = mlflow.pyfunc.load_model("text2text")
    # model_config will be applied
    result = pyfunc_loaded.predict(data)

    # overriding some inference configuration with diferent values
    pyfunc_loaded = mlflow.pyfunc.load_model(
        "text2text", model_config=dict(do_sample=False)
    )

.. note::
    Note that in the previous example, the user can't override the configuration ``do_sample``
    when calling ``predict``.

* Specifying params at inference time

.. code-block:: python

    import mlflow
    from mlflow.models import infer_signature
    from mlflow.transformers import generate_signature_output
    import transformers

    architecture = "mrm8488/t5-base-finetuned-common_gen"
    model = transformers.pipeline(
        task="text2text-generation",
        tokenizer=transformers.T5TokenizerFast.from_pretrained(architecture),
        model=transformers.T5ForConditionalGeneration.from_pretrained(architecture),
    )
    data = "pencil draw paper"

    # Define an model_config
    model_config = {
        "num_beams": 5,
        "remove_invalid_values": True,
    }

    # Define the inference parameters params
    inference_params = {
        "max_length": 30,
        "do_sample": True,
    }

    # Infer the signature including params
    signature_with_params = infer_signature(
        data,
        generate_signature_output(model, data),
        params=inference_params,
    )

    # Saving model with signature and model config
    mlflow.transformers.save_model(
        model,
        path="text2text",
        model_config=model_config,
        signature=signature_with_params,
    )

    pyfunc_loaded = mlflow.pyfunc.load_model("text2text")

    # Pass params at inference time
    params = {
        "max_length": 20,
        "do_sample": False,
    }

    # In this case we only override max_length and do_sample,
    # other params will use the default one saved on ModelSignature
    # or in the model configuration.
    # The final params used for prediction is as follows:
    # {
    #    "num_beams": 5,
    #    "max_length": 20,
    #    "do_sample": False,
    #    "remove_invalid_values": True,
    # }
    result = pyfunc_loaded.predict(data, params=params)


Example of loading a transformers model as a python function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the below example, a simple pre-trained model is used within a pipeline. After logging to MLflow, the pipeline is
loaded as a ``pyfunc`` and used to generate a response from a passed-in list of strings.

.. code-block:: python

    import mlflow
    import transformers

    # Read a pre-trained conversation pipeline from HuggingFace hub
    conversational_pipeline = transformers.pipeline(model="microsoft/DialoGPT-medium")

    # Define the signature
    signature = mlflow.models.infer_signature(
        "Hi there, chatbot!",
        mlflow.transformers.generate_signature_output(
            conversational_pipeline, "Hi there, chatbot!"
        ),
    )

    # Log the pipeline
    with mlflow.start_run():
        model_info = mlflow.transformers.log_model(
            transformers_model=conversational_pipeline,
            artifact_path="chatbot",
            task="conversational",
            signature=signature,
            input_example="A clever and witty question",
        )

    # Load the saved pipeline as pyfunc
    chatbot = mlflow.pyfunc.load_model(model_uri=model_info.model_uri)

    # Ask the chatbot a question
    response = chatbot.predict("What is machine learning?")

    print(response)

    # >> [It's a new thing that's been around for a while.]


Save and Load options for transformers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``transformers`` flavor for MLflow provides support for saving either components of a model or a pipeline object that contains the customized components in
an easy to use interface that is optimized for inference.

.. note::
    MLflow by default uses a 500 MB `max_shard_size` to save the model object in :py:func:`mlflow.transformers.save_model()` or :py:func:`mlflow.transformers.log_model()` APIs. You can use the environment variable `MLFLOW_HUGGINGFACE_MODEL_MAX_SHARD_SIZE` to override the value.

.. note::
    For component-based logging, the only requirement that must be met in the submitted ``dict`` is that a model is provided. All other elements of the ``dict`` are optional.

Logging a components-based model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The example below shows logging components of a ``transformers`` model via a dictionary mapping of specific named components. The names of the keys within the submitted dictionary
must be in the set: ``{"model", "tokenizer", "feature_extractor", "image_processor"}``. Processor type objects (some image processors, audio processors, and multi-modal processors)
must be saved explicitly with the ``processor`` argument in the :py:func:`mlflow.transformers.save_model()` or :py:func:`mlflow.transformers.log_model()` APIs.

After logging, the components are automatically inserted into the appropriate ``Pipeline`` type for the task being performed and are returned, ready for inference.

.. note::
    The components that are logged can be retrieved in their original structure (a dictionary) by setting the attribute ``return_type`` to "components" in the ``load_model()`` API.

.. attention::
    Not all model types are compatible with the pipeline API constructor via component elements. Incompatible models will raise an
    ``MLflowException`` error stating that the model is missing the `name_or_path` attribute. In
    the event that this occurs, please construct the model directly via the ``transformers.pipeline(<repo name>)`` API and save the pipeline object directly.

.. code-block:: python

    import mlflow
    import transformers

    task = "text-classification"
    architecture = "distilbert-base-uncased-finetuned-sst-2-english"
    model = transformers.AutoModelForSequenceClassification.from_pretrained(architecture)
    tokenizer = transformers.AutoTokenizer.from_pretrained(architecture)

    # Define the components of the model in a dictionary
    transformers_model = {"model": model, "tokenizer": tokenizer}

    # Log the model components
    with mlflow.start_run():
        model_info = mlflow.transformers.log_model(
            transformers_model=transformers_model,
            artifact_path="text_classifier",
            task=task,
        )

    # Load the components as a pipeline
    loaded_pipeline = mlflow.transformers.load_model(
        model_info.model_uri, return_type="pipeline"
    )

    print(type(loaded_pipeline).__name__)
    # >> TextClassificationPipeline

    loaded_pipeline(["MLflow is awesome!", "Transformers is a great library!"])

    # >> [{'label': 'POSITIVE', 'score': 0.9998478889465332},
    # >>  {'label': 'POSITIVE', 'score': 0.9998030066490173}]


Saving a pipeline and loading components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some use cases can benefit from the simplicity of defining a solution as a pipeline, but need the component-level access for performing a micro-services based deployment strategy
where pre / post-processing is performed on containers that do not house the model itself. For this paradigm, a pipeline can be loaded as its constituent parts, as shown below.

.. code-block:: python

    import transformers
    import mlflow

    translation_pipeline = transformers.pipeline(
        task="translation_en_to_fr",
        model=transformers.T5ForConditionalGeneration.from_pretrained("t5-small"),
        tokenizer=transformers.T5TokenizerFast.from_pretrained(
            "t5-small", model_max_length=100
        ),
    )

    with mlflow.start_run():
        model_info = mlflow.transformers.log_model(
            transformers_model=translation_pipeline,
            artifact_path="french_translator",
        )

    translation_components = mlflow.transformers.load_model(
        model_info.model_uri, return_type="components"
    )

    for key, value in translation_components.items():
        print(f"{key} -> {type(value).__name__}")

    # >> task -> str
    # >> model -> T5ForConditionalGeneration
    # >> tokenizer -> T5TokenizerFast

    response = translation_pipeline("MLflow is great!")

    print(response)

    # >> [{'translation_text': 'MLflow est formidable!'}]

    reconstructed_pipeline = transformers.pipeline(**translation_components)

    reconstructed_response = reconstructed_pipeline(
        "transformers makes using Deep Learning models easy and fun!"
    )

    print(reconstructed_response)

    # >> [{'translation_text': "Les transformateurs rendent l'utilisation de modèles Deep Learning facile et amusante!"}]


Automatic Metadata and ModelCard logging
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to provide as much information as possible for saved models, the ``transformers`` flavor will automatically fetch the ``ModelCard`` for any model or pipeline that
is saved that has a stored card on the HuggingFace hub. This card will be logged as part of the model artifact, viewable at the same directory level as the ``MLmodel`` file and
the stored model object.

In addition to the ``ModelCard``, the components that comprise any Pipeline (or the individual components if saving a dictionary of named components) will have their source types
stored. The model type, pipeline type, task, and classes of any supplementary component (such as a ``Tokenizer`` or ``ImageProcessor``) will be stored in the ``MLmodel`` file as well.

Automatic Signature inference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For pipelines that support ``pyfunc``, there are 3 means of attaching a model signature to the ``MLmodel`` file.

* Provide a model signature explicitly via setting a valid ``ModelSignature`` to the ``signature`` attribute. This can be generated via the helper utility :py:func:`mlflow.transformers.generate_signature_output()`

* Provide an ``input_example``. The signature will be inferred and validated that it matches the appropriate input type. The output type will be validated by performing inference automatically (if the model is a ``pyfunc`` supported type).

* Do nothing. The ``transformers`` flavor will automatically apply the appropriate general signature that the pipeline type supports (only for a single-entity; collections will not be inferred).


Scalability for inference
~~~~~~~~~~~~~~~~~~~~~~~~~

A common configuration for lowering the total memory pressure for pytorch models within ``transformers`` pipelines is to modify the
processing data type. This is achieved through setting the ``torch_dtype`` argument when creating a ``Pipeline``.
For a full reference of these tunable arguments for configuration of pipelines, see the `training docs <https://huggingface.co/docs/transformers/v4.28.1/en/perf_train_gpu_one#floating-data-types>`_ .

.. note:: This feature does not exist in versions of ``transformers`` < 4.26.x

In order to apply these configurations to a saved or logged run, there are two options:

* Save a pipeline with the `torch_dtype` argument set to the encoding type of your choice.

Example:

.. code-block:: python

    import transformers
    import torch
    import mlflow

    task = "translation_en_to_fr"

    my_pipeline = transformers.pipeline(
        task=task,
        model=transformers.T5ForConditionalGeneration.from_pretrained("t5-small"),
        tokenizer=transformers.T5TokenizerFast.from_pretrained(
            "t5-small", model_max_length=100
        ),
        framework="pt",
        torch_dtype=torch.bfloat16,
    )

    with mlflow.start_run():
        model_info = mlflow.transformers.log_model(
            transformers_model=my_pipeline,
            artifact_path="my_pipeline",
        )

    # Illustrate that the torch data type is recorded in the flavor configuration
    print(model_info.flavors["transformers"])


Result:

.. code-block:: bash

    {'transformers_version': '4.28.1',
     'code': None,
     'task': 'translation_en_to_fr',
     'instance_type': 'TranslationPipeline',
     'source_model_name': 't5-small',
     'pipeline_model_type': 'T5ForConditionalGeneration',
     'framework': 'pt',
     'torch_dtype': 'torch.bfloat16',
     'tokenizer_type': 'T5TokenizerFast',
     'components': ['tokenizer'],
     'pipeline': 'pipeline'}


* Specify the `torch_dtype` argument when loading the model to override any values set during logging or saving.

Example:

.. code-block:: python

    import transformers
    import torch
    import mlflow

    task = "translation_en_to_fr"

    my_pipeline = transformers.pipeline(
        task=task,
        model=transformers.T5ForConditionalGeneration.from_pretrained("t5-small"),
        tokenizer=transformers.T5TokenizerFast.from_pretrained(
            "t5-small", model_max_length=100
        ),
        framework="pt",
        torch_dtype=torch.bfloat16,
    )

    with mlflow.start_run():
        model_info = mlflow.transformers.log_model(
            transformers_model=my_pipeline,
            artifact_path="my_pipeline",
        )

    loaded_pipeline = mlflow.transformers.load_model(
        model_info.model_uri, return_type="pipeline", torch_dtype=torch.float64
    )

    print(loaded_pipeline.torch_dtype)


Result:

.. code-block:: bash

    torch.float64


.. note:: Logging or saving a model in 'components' mode (using a dictionary to declare components) does not support setting the data type for a constructed pipeline.
    If you need to override the default behavior of how data is encoded, please save or log a `pipeline` object.

.. note:: Overriding the data type for a pipeline when loading as a :ref:`python_function (pyfunc) model flavor <pyfunc-model-flavor>` is not supported.
    The value set for ``torch_dtype`` during ``save_model()`` or ``log_model()`` will persist when loading as `pyfunc`.

Input data types for audio pipelines
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Note that passing raw data to an audio pipeline (raw bytes) requires two separate elements of the same effective library.
In order to use the bitrate transposition and conversion of the audio bytes data into numpy nd.array format, the library `ffmpeg` is required.
Installing this package directly from pypi (`pip install ffmpeg`) does not install the underlying `c` dll's that are required to make `ffmpeg` function.
Please consult with the documentation at `the ffmpeg website <https://ffmpeg.org/download.html>`_ for guidance on your given operating system.

The Audio Pipeline types, when loaded as a :ref:`python_function (pyfunc) model flavor <pyfunc-model-flavor>` have three input types available:

* ``str``

The string input type is meant for blob references (uri locations) that are accessible to the instance of the ``pyfunc`` model.
This input mode is useful when doing large batch processing of audio inference in Spark due to the inherent limitations of handling large ``bytes``
data in ``Spark`` ``DataFrames``. Ensure that you have ``ffmpeg`` installed in the environment that the ``pyfunc`` model is running in order
to use ``str`` input uri-based inference. If this package is not properly installed (both from ``pypi`` and from the ``ffmpeg`` binaries), an Exception
will be thrown at inference time.

.. warning:: If using a uri (`str`) as an input type for a `pyfunc` model that you are intending to host for realtime inference through the `MLflow Model Server`,
    you *must* specify a custom model signature when logging or saving the model.
    The default signature input value type of ``bytes`` will, in `MLflow Model serving`, force the conversion of the uri string to ``bytes``, which will cause an Exception
    to be thrown from the serving process stating that the soundfile is corrupt.

An example of specifying an appropriate uri-based input model signature for an audio model is shown below:

.. code-block:: python

    from mlflow.models import infer_signature
    from mlflow.transformers import generate_signature_output

    url = "https://www.mywebsite.com/sound/files/for/transcription/file111.mp3"
    signature = infer_signature(url, generate_signature_output(my_audio_pipeline, url))
    with mlflow.start_run():
        mlflow.transformers.log_model(
            transformers_model=my_audio_pipeline,
            artifact_path="my_transcriber",
            signature=signature,
        )


* ``bytes``

This is the default serialization format of audio files. It is the easiest format to utilize due to the fact that
Pipeline implementations will automatically convert the audio bitrate from the file with the use of ``ffmpeg`` (a required dependency if using this format) to the bitrate required by the underlying model within the `Pipeline`.
When using the ``pyfunc`` representation of the pipeline directly (not through serving), the sound file can be passed directly as ``bytes`` without any
modification. When used through serving, the ``bytes`` data *must be* base64 encoded.

* ``np.ndarray``

This input format requires that both the bitrate has been set prior to conversion to ``numpy.ndarray`` (i.e., through the use of a package like
``librosa`` or ``pydub``) and that the model has been saved with a signature that uses the ``np.ndarray`` format for the input.

.. note:: Audio models being used for serving that intend to utilize pre-formatted audio in ``np.ndarray`` format
    must have the model saved with a signature configuration that reflects this schema. Failure to do so will result in type casting errors due to the default signature for
    audio transformers pipelines being set as expecting ``binary`` (``bytes``) data. The serving endpoint cannot accept a union of types, so a particular model instance must choose one
    or the other as an allowed input type.