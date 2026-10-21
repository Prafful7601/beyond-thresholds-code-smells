# Error-analysis samples (best model, repeat-0 out-of-fold predictions)

## CM FP M144190 (MyCATApache_Mycat-Server); votes 0/2; in run: False; score 0.530

`/codesplit_java_method/MyCATApache_Mycat-Server/MyCATApache_Mycat-Server/io.mycat.backend.jdbc.sequoiadb/SequoiaSQLParser/opSQLExpr.code`

```java
@SuppressWarnings("unused") private void opSQLExpr(SQLBinaryOpExpr expr,BasicBSONObject o){
  SQLExpr exprL=expr.getLeft();
  if (!(exprL instanceof SQLBinaryOpExpr)) {
    if (expr.getOperator().getName().equals("=")) {
      o.put(exprL.toString(),getExpValue(expr.getRight()));
    }
 else {
      String op="";
      if (expr.getOperator().getName().equals("<")) {
        op="$lt";
      }
      if (expr.getOperator().getName().equals("<=")) {
        op="$lte";
      }
      if (expr.getOperator().getName().equals(">")) {
        op="$gt";
      }
      if (expr.getOperator().getName().equals(">=")) {
        op="$gte";
      }
      if (expr.getOperator().getName().equals("!=")) {
        op="$ne";
      }
      if (expr.getOperator().getName().equals("<>")) {
        op="$ne";
      }
      parserDBObject(o,exprL.toString(),op,getExpValue(expr.getRight()));
    }
  }
}
```

## CM FP M145334 (MyCATApache_Mycat-Server); votes 0/2; in run: False; score 0.519

`/codesplit_java_method/MyCATApache_Mycat-Server/MyCATApache_Mycat-Server/io.mycat.catlets/TableFilter/addField.code`

```java
public void addField(String fieldName,String fieldAlia){
  String atable=getTablefrom(fieldName);
  String afield=getFieldfrom(fieldName);
  boolean allfield=afield.equals("*") ? true : false;
  if (atable.equals("*")) {
    fieldAliasMap.put(afield,null);
    setAllField(allfield);
    if (join != null) {
      join.addField(fieldName,null);
      join.setAllField(allfield);
    }
  }
 else {
    if (atable.equals(tAlia)) {
      fieldAliasMap.put(afield,fieldAlia);
      setAllField(allfield);
    }
 else {
      if (join != null) {
        join.addField(fieldName,fieldAlia);
        join.setAllField(allfield);
      }
    }
  }
}
public void addField(String fieldName,String fieldAlia,String expr){
  String atable=getTablefrom(fieldName);
  String afield=getFieldfrom(fieldName);
  boolean allfield=afield.equals("*") ? true : false;
  if (atable.equals("*")) {
    fieldAliasMap.put(afield,null);
    setAllField(allfield);
    if (join != null) {
      join.addField(fieldName,null);
      join.setAllField(allfield);
    }
  }
 else {
    if (atable.equals(tAlia)) {
      expr=expr.replace(fieldName,afield);
      fieldAliasMap.put(expr,fieldAlia);
      setAllField(allfield);
    }
 else {
      if (join != null) {
        join.addField(fieldName,fieldAlia,expr);
        join.setAllField(allfield);
      }
    }
  }
}
```

## CM FP M145369 (MyCATApache_Mycat-Server); votes 0/2; in run: False; score 0.509

`/codesplit_java_method/MyCATApache_Mycat-Server/MyCATApache_Mycat-Server/io.mycat.config/ConfigInitializer/testConnection.code`

```java
public void testConnection(){
  if (this.dataNodes != null && this.dataHosts != null) {
    Map<String,Boolean> map=new HashMap<String,Boolean>();
    for (    PhysicalDBNode dataNode : dataNodes.values()) {
      String database=dataNode.getDatabase();
      PhysicalDBPool pool=dataNode.getDbPool();
      for (      PhysicalDatasource ds : pool.getAllDataSources()) {
        String key=ds.getName() + "_" + database;
        if (map.get(key) == null) {
          map.put(key,false);
          boolean isConnected=false;
          try {
            isConnected=ds.testConnection(database);
            map.put(key,isConnected);
          }
 catch (          IOException e) {
            LOGGER.warn("test conn error:",e);
          }
        }
      }
    }
    boolean isConnectivity=true;
    for (    Map.Entry<String,Boolean> entry : map.entrySet()) {
      String key=entry.getKey();
      Boolean value=entry.getValue();
      if (!value && isConnectivity) {
        LOGGER.warn("SelfCheck### test " + key + " database connection failed ");
        isConnectivity=false;
      }
 else {
        LOGGER.info("SelfCheck### test " + key + " database connection success ");
      }
    }
    if (!isConnectivity) {
      throw new ConfigException("SelfCheck### there are some datasource connection failed, pls check!");
    }
  }
}
```

## CM FP M148118 (MyCATApache_Mycat-Server); votes 0/2; in run: True; score 0.557

`/codesplit_java_method/MyCATApache_Mycat-Server/MyCATApache_Mycat-Server/io.mycat.route.function/PartitionByCRC32PreSlot/hashTest.code`

```java
private static void hashTest() throws IOException {
  PartitionByCRC32PreSlot hash=new PartitionByCRC32PreSlot();
  hash.setRuleName("test");
  RuleConfig rule=new RuleConfig("id","crc32slot");
  int count=1024;
  String sb=genDataNodesString(count);
  TableConfig tableConf=new TableConfig("test","id",true,false,-1,sb,null,rule,true,null,false,null,null,null,false);
  hash.setTableConfig(tableConf);
  hash.reInit();
  long start=System.currentTimeMillis();
  int[] bucket=new int[hash.getCount()];
  Map<Integer,List<Integer>> hashed=new HashMap<>();
  int total=1000_0000;
  int c=0;
  for (int i=100_0000; i < total + 100_0000; i++) {
    c++;
    int h=hash.calculate(StringUtil.removeBackquote(Integer.toString(i)));
    if (h >= count) {
      System.out.println("error:" + h);
    }
    bucket[h]++;
    List<Integer> list=hashed.get(h);
    if (list == null) {
      list=new ArrayList<>();
      hashed.put(h,list);
    }
    list.add(i);
  }
  System.out.println(c + "   " + total);
  double d=0;
  c=0;
  int idx=0;
  System.out.println("index    bucket   ratio");
  for (  int i : bucket) {
    d+=i / (double)total;
    c+=i;
    System.out.println(idx++ + "  " + i+ "   "+ (i / (double)total));
  }
  System.out.println(d + "  " + c);
  long used=System.currentTimeMillis() - start;
  System.out.println("tps " + total * 1000.0 / used);
  System.out.println("****************************************************");
}
```

## CM FP M148671 (MyCATApache_Mycat-Server); votes 0/2; in run: True; score 0.518

`/codesplit_java_method/MyCATApache_Mycat-Server/MyCATApache_Mycat-Server/io.mycat.route.parser.druid/MycatSchemaStatVisitor/sqlConditionListEquals.code`

```java
/** 
 * 判定两个条件列表的元素是否内容相等
 * @author SvenAugustus
 * @param list1
 * @param list2
 * @return
 */
private boolean sqlConditionListEquals(List<Condition> list1,List<Condition> list2){
  if (list1 == null) {
    if (list2 != null) {
      return false;
    }
    return true;
  }
  if (list2.size() != list1.size()) {
    return false;
  }
  int len=list1.size();
  for (int j=0; j < len; j++) {
    boolean exists=false;
    for (int i=0; i < len; i++) {
      if (sqlConditionEquals(list2.get(j),list1.get(i))) {
        exists=true;
        break;
      }
    }
    if (!exists) {
      return false;
    }
  }
  return true;
}
```

## CM FP M150088 (MyCATApache_Mycat-Server); votes 0/2; in run: False; score 0.508

`/codesplit_java_method/MyCATApache_Mycat-Server/MyCATApache_Mycat-Server/io.mycat.util/RandomUtil/getNRandom.code`

```java
/** 
 * 随机指定范围内N个不重复的数 最简单最基本的方法
 * @param min 指定范围最小值（包含）
 * @param max 指定范围最大值(不包含)
 * @param n 随机数个数
 */
public static int[] getNRandom(int min,int max,int n){
  if (n > (max - min + 1) || max < min) {
    return null;
  }
  int[] result=new int[n];
  for (int i=0; i < n; i++) {
    result[i]=-9999;
  }
  int count=0;
  while (count < n) {
    int num=(int)((Math.random() * (max - min)) + min);
    boolean flag=true;
    for (int j=0; j < n; j++) {
      if (num == result[j]) {
        flag=false;
        break;
      }
    }
    if (flag) {
      result[count]=num;
      count++;
    }
  }
  return result;
}
```

## CM FP M157485 (igniterealtime_Smack); votes 0/2; in run: True; score 0.632

`/codesplit_java_method/igniterealtime_Smack/igniterealtime_Smack/org.jivesoftware.smackx.privacy/PrivacyListManager/PrivacyListManager.code`

```java
/** 
 * Creates a new privacy manager to maintain the communication privacy. Note: no information is sent to or received from the server until you attempt to get or set the privacy communication.<p>
 * @param connection the XMPP connection.
 */
private PrivacyListManager(XMPPConnection connection){
  super(connection);
  connection.registerIQRequestHandler(new AbstractIqRequestHandler(Privacy.ELEMENT,Privacy.NAMESPACE,IQ.Type.set,Mode.sync){
    @Override public IQ handleIQRequest(    IQ iqRequest){
      Privacy privacy=(Privacy)iqRequest;
      for (      PrivacyListListener listener : listeners) {
        for (        Map.Entry<String,List<PrivacyItem>> entry : privacy.getItemLists().entrySet()) {
          String listName=entry.getKey();
          List<PrivacyItem> items=entry.getValue();
          if (items.isEmpty()) {
            listener.updatedPrivacyList(listName);
          }
 else {
            listener.setPrivacyList(listName,items);
          }
        }
      }
      return IQ.createResultIQ(privacy);
    }
  }
);
  connection.addStanzaSendingListener(new StanzaListener(){
    @Override public void processStanza(    Stanza packet) throws NotConnectedException {
      XMPPConnection connection=connection();
      Privacy privacy=(Privacy)packet;
      StanzaFilter iqResultReplyFilter=new IQResultReplyFilter(privacy,connection);
      final String activeListName=privacy.getActiveName();
      final boolean declinceActiveList=privacy.isDeclineActiveList();
      connection.addOneTimeSyncCallback(new StanzaListener(){
        @Override public void processStanza(        Stanza packet) throws NotConnectedException {
          if (declinceActiveList) {
            cachedActiveListName=null;
          }
 else {
            cachedActiveListName=activeListName;
          }
          return;
        }
      }
,iqResultReplyFilter);
    }
  }
,SetActiveListFilter.INSTANCE);
  connection.addStanzaSendingListener(new StanzaListener(){
    @Override public void processStanza(    Stanza packet) throws NotConnectedException {
      XMPPConnection connection=connection();
      Privacy privacy=(Privacy)packet;
      StanzaFilter iqResultReplyFilter=new IQResultReplyFilter(privacy,connection);
      final String defaultListName=privacy.getDefaultName();
      final boolean declinceDefaultList=privacy.isDeclineDefaultList();
      connection.addOneTimeSyncCallback(new StanzaListener(){
        @Override public void processStanza(        Stanza packet) throws NotConnectedException {
          if (declinceDefaultList) {
            cachedDefaultListName=null;
          }
 else {
            cachedDefaultListName=defaultListName;
          }
          return;
        }
      }
,iqResultReplyFilter);
    }
  }
,SetDefaultListFilter.INSTANCE);
  connection.addSyncStanzaListener(new StanzaListener(){
    @Override public void processStanza(    Stanza packet) throws NotConnectedException {
      Privacy privacy=(Privacy)packet;
      String activeList=privacy.getActiveName();
      if (activeList != null) {
        cachedActiveListName=activeList;
      }
      String defaultList=privacy.getDefaultName();
      if (defaultList != null) {
        cachedDefaultListName=defaultList;
      }
    }
  }
,PRIVACY_RESULT);
  connection.addConnectionListener(new ConnectionListener(){
    @Override public void authenticated(    XMPPConnection connection,    boolean resumed){
      if (resumed) {
        return;
      }
      cachedActiveListName=cachedDefaultListName=null;
    }
  }
);
  ServiceDiscoveryManager.getInstanceFor(connection).addFeature(NAMESPACE);
}
```

## CM FP M162690 (lettuce-io_lettuce-core); votes 0/2; in run: False; score 0.596

`/codesplit_java_method/lettuce-io_lettuce-core/lettuce-io_lettuce-core/io.lettuce.core/ConnectionBuilder/configureBootstrap.code`

```java
/** 
 * Initialize the  {@link Bootstrap}.
 * @since 6.1
 */
public void configureBootstrap(boolean domainSocket,Function<Class<? extends EventLoopGroup>,EventLoopGroup> eventLoopGroupProvider){
  LettuceAssert.assertState(bootstrap != null,"Bootstrap must be set");
  LettuceAssert.assertState(clientOptions != null,"ClientOptions must be set");
  Class<? extends EventLoopGroup> eventLoopGroupClass=Transports.eventLoopGroupClass();
  Class<? extends Channel> channelClass=Transports.socketChannelClass();
  if (domainSocket) {
    Transports.NativeTransports.assertDomainSocketAvailable();
    eventLoopGroupClass=Transports.NativeTransports.eventLoopGroupClass();
    channelClass=Transports.NativeTransports.domainSocketChannelClass();
  }
 else {
    bootstrap.resolver(clientResources.addressResolverGroup());
  }
  SocketOptions options=clientOptions.getSocketOptions();
  EventLoopGroup eventLoopGroup=eventLoopGroupProvider.apply(eventLoopGroupClass);
  bootstrap.option(ChannelOption.CONNECT_TIMEOUT_MILLIS,Math.toIntExact(options.getConnectTimeout().toMillis()));
  if (!domainSocket) {
    bootstrap.option(ChannelOption.SO_KEEPALIVE,options.isKeepAlive());
    bootstrap.option(ChannelOption.TCP_NODELAY,options.isTcpNoDelay());
  }
  bootstrap.channel(channelClass).group(eventLoopGroup);
  if (options.isKeepAlive() && options.isExtendedKeepAlive()) {
    SocketOptions.KeepAliveOptions keepAlive=options.getKeepAlive();
    if (IOUringProvider.isAvailable()) {
      IOUringProvider.applyKeepAlive(bootstrap,keepAlive.getCount(),keepAlive.getIdle(),keepAlive.getInterval());
    }
 else     if (io.lettuce.core.resource.EpollProvider.isAvailable()) {
      EpollProvider.applyKeepAlive(bootstrap,keepAlive.getCount(),keepAlive.getIdle(),keepAlive.getInterval());
    }
 else     if (ExtendedNioSocketOptions.isAvailable() && !KqueueProvider.isAvailable()) {
      ExtendedNioSocketOptions.applyKeepAlive(bootstrap,keepAlive.getCount(),keepAlive.getIdle(),keepAlive.getInterval());
    }
 else {
      logger.warn("Cannot apply extended TCP keepalive options to channel type " + channelClass.getName());
    }
  }
}
```

## CM FP M174981 (kevin-wayne_algs4); votes 0/2; in run: False; score 0.509

`/codesplit_java_method/kevin-wayne_algs4/kevin-wayne_algs4/edu.princeton.cs.algs4/FlowEdge/addResidualFlowTo.code`

```java
/** 
 * Increases the flow on the edge in the direction to the given vertex. If  {@code vertex} is the tail vertex, this increases the flow on the edge by {@code delta}; if  {@code vertex} is the head vertex, this decreases the flow on the edge by {@code delta}.
 * @param vertex one endpoint of the edge
 * @param delta amount by which to increase flow
 * @throws IllegalArgumentException if {@code vertex} is not one of the endpointsof the edge
 * @throws IllegalArgumentException if {@code delta} makes the flowon the edge either negative or larger than its capacity
 * @throws IllegalArgumentException if {@code delta} is {@code NaN}
 */
public void addResidualFlowTo(int vertex,double delta){
  if (!(delta >= 0.0))   throw new IllegalArgumentException("Delta must be non-negative");
  if (vertex == v)   flow-=delta;
 else   if (vertex == w)   flow+=delta;
 else   throw new IllegalArgumentException("invalid endpoint");
  if (Math.abs(flow) <= FLOATING_POINT_EPSILON)   flow=0;
  if (Math.abs(flow - capacity) <= FLOATING_POINT_EPSILON)   flow=capacity;
  if (!(flow >= 0.0))   throw new IllegalArgumentException("Flow is negative");
  if (!(flow <= capacity))   throw new IllegalArgumentException("Flow exceeds capacity");
}
```

## CM FP M180379 (MovingBlocks_Terasology); votes 0/2; in run: False; score 0.602

`/codesplit_java_method/MovingBlocks_Terasology/MovingBlocks_Terasology/org.terasology.engine.logic.console.ui/CyclingTabCompletionEngine/complete.code`

```java
@Override public String complete(String rawCommand){
  if (rawCommand.length() <= 0) {
    reset();
    previousMessage=new Message("Type 'help' to list all commands.");
    console.addMessage(previousMessage);
    return null;
  }
 else   if (query == null) {
    query=rawCommand;
  }
  String commandNameRaw=console.processCommandName(query);
  Name commandName=new Name(commandNameRaw);
  List<String> commandParameters=console.processParameters(query);
  ConsoleCommand command=console.getCommand(commandName);
  int suggestedIndex=commandParameters.size() + (query.charAt(query.length() - 1) == ' ' ? 1 : 0);
  Set<String> matches=findMatches(commandName,commandParameters,command,suggestedIndex);
  if (matches == null || matches.size() <= 0) {
    return query;
  }
  if (previousMatches == null || !matches.equals(Sets.newHashSet(previousMatches))) {
    reset(false);
    if (matches.size() == 1) {
      return generateResult(matches.iterator().next(),commandName,commandParameters,suggestedIndex);
    }
    previousMatches=Lists.newArrayList(matches);
    Collections.sort(previousMatches);
  }
  StringBuilder matchMessageString=new StringBuilder();
  for (int i=0; i < previousMatches.size(); i++) {
    if (i > 0) {
      matchMessageString.append(' ');
    }
    String match=previousMatches.get(i);
    if (selectionIndex == i) {
      match=FontColor.getColored(match,ConsoleColors.COMMAND);
    }
    matchMessageString.append(match);
  }
  Message matchMessage=new Message(matchMessageString.toString());
  String suggestion=previousMatches.get(selectionIndex);
  if (previousMessage != null) {
    console.replaceMessage(previousMessage,matchMessage);
  }
 else {
    console.addMessage(matchMessage);
  }
  previousMessage=matchMessage;
  selectionIndex=(selectionIndex + 1) % previousMatches.size();
  return generateResult(suggestion,commandName,commandParameters,suggestedIndex);
}
```

## CM FP M182134 (MovingBlocks_Terasology); votes 0/2; in run: False; score 0.640

`/codesplit_java_method/MovingBlocks_Terasology/MovingBlocks_Terasology/org.terasology.engine.persistence.typeHandling.gson/PolymorphicTypeAdapterFactory/create.code`

```java
@Override public <R>TypeAdapter<R> create(Gson gson,TypeToken<R> type){
  if (!baseClass.isAssignableFrom(type.getRawType())) {
    return null;
  }
  return new TypeAdapter<R>(){
    @SuppressWarnings("unchecked") @Override public void write(    JsonWriter out,    R value) throws IOException {
      Class<?> valueClass=value.getClass();
      String valueTypeName=valueClass.getName();
      TypeToken<?> valueType=TypeToken.get(valueClass);
      TypeAdapter<R> delegate=(TypeAdapter<R>)gson.getDelegateAdapter(PolymorphicTypeAdapterFactory.this,valueType);
      if (delegate == null) {
        throw new JsonParseException("Could not serialize " + valueClass.getName());
      }
      JsonElement jsonElement=delegate.toJsonTree(value);
      if (valueClass != baseClass) {
        JsonObject jsonObject=jsonElement.getAsJsonObject();
        JsonObject clone=new JsonObject();
        clone.add(TYPE_FIELD_NAME,new JsonPrimitive(valueTypeName));
        for (        Map.Entry<String,JsonElement> e : jsonObject.entrySet()) {
          clone.add(e.getKey(),e.getValue());
        }
        Streams.write(clone,out);
      }
 else {
        Streams.write(jsonElement,out);
      }
    }
    @SuppressWarnings("unchecked") @Override public R read(    JsonReader in) throws IOException {
      JsonElement jsonElement=Streams.parse(in);
      Class<?> valueClass;
      if (jsonElement.isJsonObject()) {
        JsonElement typeNameJsonElement=jsonElement.getAsJsonObject().remove(TYPE_FIELD_NAME);
        if (typeNameJsonElement != null) {
          String typeName=typeNameJsonElement.getAsString();
          try {
            valueClass=Class.forName(typeName);
          }
 catch (          ClassNotFoundException e) {
            throw new JsonParseException("Could not find class " + typeName);
          }
        }
 else {
          valueClass=baseClass;
        }
      }
 else {
        valueClass=baseClass;
      }
      if (!baseClass.isAssignableFrom(valueClass)) {
        throw new JsonParseException(valueClass.getName() + " does not derive from " + baseClass.getName());
      }
      TypeToken<?> valueType=TypeToken.get(valueClass);
      TypeAdapter<R> delegate=(TypeAdapter<R>)gson.getDelegateAdapter(PolymorphicTypeAdapterFactory.this,valueType);
      if (delegate == null) {
        throw new JsonParseException("Could not deserialize " + valueClass.getName());
      }
      return delegate.fromJsonTree(jsonElement);
    }
  }
;
}
```

## CM FP M182831 (MovingBlocks_Terasology); votes 0/2; in run: False; score 0.704

`/codesplit_java_method/MovingBlocks_Terasology/MovingBlocks_Terasology/org.terasology.engine.rendering.assets.atlas/AtlasFormat/process.code`

```java
private void process(FreeformDefinition freeform,Texture texture,Vector2ic size,Map<Name,SubtextureData> out){
  if (freeform.getName() == null || freeform.getName().isEmpty()) {
    logger.error("Bad subimage definition - missing mandatory property name");
    return;
  }
  if (freeform.getMin() == null) {
    logger.error("Bad subimage definition '{}' - missing mandatory property min",freeform.getName());
    return;
  }
  if (freeform.getSize() == null && freeform.getMax() == null) {
    logger.error("Bad subimage definition '{}' - requires one of max or size",freeform.getName());
    return;
  }
  Vector2f min=new Vector2f((float)freeform.getMin().x / size.x(),(float)freeform.getMin().y / size.y());
  if (freeform.getSize() != null) {
    Vector2f itemSize=new Vector2f((float)freeform.getSize().x / size.x(),(float)freeform.getSize().y / size.y());
    out.put(new Name(freeform.getName()),new SubtextureData(texture,shrinkRegion(new Rectanglef(min,min).setSize(itemSize))));
  }
 else   if (freeform.getMax() != null) {
    Vector2f max=new Vector2f((float)freeform.getMax().x / size.x(),(float)freeform.getMax().y / size.y());
    out.put(new Name(freeform.getName()),new SubtextureData(texture,shrinkRegion(new Rectanglef(min,max))));
  }
}
private void process(GridDefinition grid,Texture texture,Vector2ic size,Map<Name,SubtextureData> out){
  if (grid.getTileSize() == null) {
    logger.error("Bad grid definition - missing mandatory property tileSize");
    return;
  }
  if (grid.getGridDimensions() == null) {
    logger.error("Bad grid definition - missing mandatory property gridDimensions");
    return;
  }
  Vector2f offset=new Vector2f(0,0);
  if (grid.getGridOffset() != null) {
    offset.set((float)grid.getGridOffset().x / size.x(),(float)grid.getGridOffset().y / size.y());
  }
  Vector2f tileSize=new Vector2f((float)grid.getTileSize().x / size.x(),(float)grid.getTileSize().y / size.y());
  int tileX=0;
  int tileY=0;
  for (  String name : grid.getTileNames()) {
    if (!name.isEmpty()) {
      Vector2f pos=new Vector2f(offset);
      pos.x+=tileX * tileSize.x;
      pos.y+=tileY * tileSize.y;
      Rectanglef tileLocation=new Rectanglef(offset.x + tileX * tileSize.x,offset.y + tileY * tileSize.y,0.0f,0.0f).setSize(tileSize.x,tileSize.y);
      out.put(new Name(name),new SubtextureData(texture,shrinkRegion(tileLocation)));
    }
    tileX++;
    if (tileX == grid.getGridDimensions().x) {
      tileX=0;
      tileY++;
    }
  }
}
```

## CM FP M183576 (MovingBlocks_Terasology); votes 0/2; in run: False; score 0.517

`/codesplit_java_method/MovingBlocks_Terasology/MovingBlocks_Terasology/org.terasology.engine.rendering.dag/RenderGraph/getNodesInTopologicalOrder.code`

```java
public List<Node> getNodesInTopologicalOrder(){
  List<Node> topologicalList=new ArrayList<>();
  postConnectAll();
  Map<Node,Integer> inDegreeMap=Maps.newHashMap();
  List<Node> nodesToExamine=Lists.newArrayList();
  int visitedNodes=0;
  for (  Node node : graph.nodes()) {
    int inDegree=graph.inDegree(node);
    inDegreeMap.put(node,inDegree);
    if (inDegree == 0) {
      nodesToExamine.add(node);
    }
  }
  while (!nodesToExamine.isEmpty()) {
    Node currentNode=nodesToExamine.remove(0);
    for (    Node adjacentNode : graph.successors(currentNode)) {
      int updatedInDegree=inDegreeMap.get(adjacentNode) - 1;
      inDegreeMap.put(adjacentNode,updatedInDegree);
      if (updatedInDegree == 0) {
        nodesToExamine.add(adjacentNode);
      }
    }
    topologicalList.add(currentNode);
    visitedNodes++;
  }
  if (visitedNodes != nodeMap.size()) {
    throw new RuntimeException("Cycle detected in the DAG: topological sorting not possible!");
  }
  topologicalList.forEach((key) -> key.postInit(context));
  return topologicalList;
}
```

## CM FP M184354 (MovingBlocks_Terasology); votes 0/2; in run: False; score 0.660

`/codesplit_java_method/MovingBlocks_Terasology/MovingBlocks_Terasology/org.terasology.engine.rendering.nui.internal/LwjglCanvasRenderer/drawTexture.code`

```java
@Override public void drawTexture(UITextureRegion texture,Colorc color,ScaleMode mode,Rectanglei absoluteRegionRectangle,float ux,float uy,float uw,float uh,float alpha){
  if (!((TextureRegion)texture).getTexture().isLoaded()) {
    return;
  }
  Rectanglei absoluteRegion=new Rectanglei(absoluteRegionRectangle);
  if (!currentTextureCropRegion.equals(requestedCropRegion) && !(currentTextureCropRegion.containsRectangle(absoluteRegion) && requestedCropRegion.containsRectangle(absoluteRegion))) {
    textureMat.setFloat4(CROPPING_BOUNDARIES_PARAM,requestedCropRegion.minX,requestedCropRegion.maxX,requestedCropRegion.minY,requestedCropRegion.maxY);
    currentTextureCropRegion=requestedCropRegion;
  }
  Vector2f scale=mode.scaleForRegion(absoluteRegionRectangle,texture.getWidth(),texture.getHeight());
  Rectanglef textureArea=new Rectanglef(texture.getRegion());
  Mesh mesh=billboard;
switch (mode) {
case TILED:
{
      Vector2i textureSize=texture.size();
      TextureCacheKey key=new TextureCacheKey(textureSize,new Vector2i(absoluteRegion.getSizeX(),absoluteRegion.getSizeY()));
      usedTextures.add(key);
      mesh=cachedTextures.get(key);
      if (mesh == null || mesh.isDisposed()) {
        MeshBuilder builder=new MeshBuilder();
        addTiles(builder,absoluteRegion,FULL_REGION,textureSize,FULL_REGION);
        mesh=builder.build();
        cachedTextures.put(key,mesh);
      }
      textureMat.setFloat2("scale",scale);
      textureMat.setFloat2("offset",absoluteRegion.minX,absoluteRegion.minY);
      textureMat.setFloat2("texOffset",textureArea.minX + ux * textureArea.getSizeX(),textureArea.minY + uy * textureArea.getSizeY());
      textureMat.setFloat2("texSize",uw * textureArea.getSizeX(),uh * textureArea.getSizeY());
      break;
    }
case SCALE_FILL:
{
    textureMat.setFloat2("offset",absoluteRegion.minX,absoluteRegion.minY);
    textureMat.setFloat2("scale",absoluteRegion.getSizeX(),absoluteRegion.getSizeY());
    float texBorderX=(scale.x - absoluteRegion.getSizeX()) / scale.x * uw;
    float texBorderY=(scale.y - absoluteRegion.getSizeY()) / scale.y * uh;
    textureMat.setFloat2("texOffset",textureArea.minX + (ux + 0.5f * texBorderX) * textureArea.getSizeX(),textureArea.minY + (uy + 0.5f * texBorderY) * textureArea.getSizeY());
    textureMat.setFloat2("texSize",(uw - texBorderX) * textureArea.getSizeX(),(uh - texBorderY) * textureArea.getSizeY());
    break;
  }
default :
{
  textureMat.setFloat2("scale",scale);
  textureMat.setFloat2("offset",absoluteRegion.minX + 0.5f * (absoluteRegion.getSizeX() - scale.x),absoluteRegion.minY + 0.5f * (absoluteRegion.getSizeY() - scale.y));
  textureMat.setFloat2("texOffset",textureArea.minX + ux * textureArea.getSizeX(),textureArea.minY + uy * textureArea.getSizeY());
  textureMat.setFloat2("texSize",uw * textureArea.getSizeX(),uh * textureArea.getSizeY());
  break;
}
}
textureMat.setTexture("tex",((TextureRegion)texture).getTexture());
textureMat.setFloat4("color",color.rf(),color.gf(),color.bf(),color.af() * alpha);
textureMat.setMatrix4("projectionMatrix",projMatrix);
textureMat.setMatrix4("modelViewMatrix",modelMatrixStack);
textureMat.bindTextures();
mesh.render();
}
```

## CM FP M185454 (MovingBlocks_Terasology); votes 0/2; in run: False; score 0.610

`/codesplit_java_method/MovingBlocks_Terasology/MovingBlocks_Terasology/org.terasology.engine.rendering.nui.widgets.types.object/SubtypeLayoutBuilder/SubtypeLayoutBuilder.code`

```java
public SubtypeLayoutBuilder(TypeInfo<T> baseType,TypeWidgetLibrary library,ModuleManager moduleManager,TypeRegistry typeRegistry){
  this.library=library;
  this.baseType=baseType;
  this.moduleManager=moduleManager;
  baseTypeWidgetBuilder=library.getBuilder(baseType).orElse(null);
  Module contextModule=ModuleContext.getContext();
  PermissionProvider permissionProvider=moduleManager.getPermissionProvider(contextModule);
  ModuleEnvironment environment=moduleManager.getEnvironment();
  Set<Name> allowedProvidingModules=ImmutableSet.<Name>builder().add(contextModule.getId()).addAll(environment.getDependencyNamesOf(contextModule.getId())).build();
  List<Class<? extends T>> allowedSubclasses=typeRegistry.getSubtypesOf(baseType.getRawType()).stream().filter(clazz -> allowedProvidingModules.contains(getModuleProviding(clazz)) || permissionProvider.isPermitted(clazz)).filter(clazz -> {
    int modifiers=clazz.getModifiers();
    return Modifier.isPublic(modifiers) && !Modifier.isAbstract(modifiers) && !clazz.isInterface();
  }
).filter(clazz -> {
    if (clazz.isLocalClass()) {
      return false;
    }
    return !clazz.isMemberClass() || Modifier.isStatic(clazz.getModifiers());
  }
).collect(Collectors.toList());
  allowedSubclasses.add(baseType.getRawType());
  for (int i=0; i < allowedSubclasses.size() - 1; i++) {
    Class<? extends T> a=allowedSubclasses.get(i);
    for (int j=i + 1; j < allowedSubclasses.size(); j++) {
      Class<? extends T> b=allowedSubclasses.get(j);
      if (!a.isAssignableFrom(b)) {
        continue;
      }
      allowedSubclasses.set(i,b);
      allowedSubclasses.set(j,a);
    }
  }
  allowedSubtypes=allowedSubclasses.stream().map(clazz -> {
    Type parameterized=ReflectionUtil.parameterizeandResolveRawType(baseType.getType(),clazz);
    return (TypeInfo<T>)TypeInfo.of(parameterized);
  }
).collect(Collectors.toList());
}
```

## CM FN M143067 (MyCATApache_Mycat-Server); votes 2/2; in run: True; score 0.445

`/codesplit_java_method/MyCATApache_Mycat-Server/MyCATApache_Mycat-Server/io.mycat.backend/ConMap/getTotalCountForDs.code`

```java
public int getTotalCountForDs(PhysicalDatasource dataSouce){
  int total=0;
  for (  NIOProcessor processor : MycatServer.getInstance().getProcessors()) {
    for (    BackendConnection con : processor.getBackends().values()) {
      if (con instanceof MySQLConnection) {
        MySQLConnection mysqlCon=(MySQLConnection)con;
        if (mysqlCon.getPool() == dataSouce && !mysqlCon.isClosed()) {
          total++;
        }
      }
 else       if (con instanceof JDBCConnection) {
        JDBCConnection jdbcCon=(JDBCConnection)con;
        if (jdbcCon.getPool() == dataSouce && !jdbcCon.isClosed()) {
          total++;
        }
      }
    }
  }
  return total;
}
```

## CM FN M143081 (MyCATApache_Mycat-Server); votes 2/2; in run: True; score 0.443

`/codesplit_java_method/MyCATApache_Mycat-Server/MyCATApache_Mycat-Server/io.mycat.backend/ConQueue/getIdleConsToClose.code`

```java
public ArrayList<BackendConnection> getIdleConsToClose(int count){
  ArrayList<BackendConnection> readyCloseCons=new ArrayList<BackendConnection>(count);
  while (!manCommitCons.isEmpty() && readyCloseCons.size() < count) {
    BackendConnection theCon=manCommitCons.poll();
    if (theCon != null && !theCon.isBorrowed()) {
      readyCloseCons.add(theCon);
    }
  }
  while (!autoCommitCons.isEmpty() && readyCloseCons.size() < count) {
    BackendConnection theCon=autoCommitCons.poll();
    if (theCon != null && !theCon.isBorrowed()) {
      readyCloseCons.add(theCon);
    }
  }
  return readyCloseCons;
}
```

## CM FN M144263 (MyCATApache_Mycat-Server); votes 2/2; in run: False; score 0.422

`/codesplit_java_method/MyCATApache_Mycat-Server/MyCATApache_Mycat-Server/io.mycat.backend.mysql/ByteUtil/readLength.code`

```java
public static long readLength(byte[] data,int offset){
  int length=data[offset++] & 0xff;
switch (length) {
case 251:
    return MySQLMessage.NULL_LENGTH;
case 252:
  return readUB2(data,offset);
case 253:
return readUB3(data,offset);
case 254:
return readLong(data,offset);
default :
return length;
}
}
```

## CM FN M148535 (MyCATApache_Mycat-Server); votes 2/2; in run: False; score 0.419

`/codesplit_java_method/MyCATApache_Mycat-Server/MyCATApache_Mycat-Server/io.mycat.route/DruidMysqlCreateTableTest/hasColumn.code`

```java
private static boolean hasColumn(SQLStatement statement){
  for (  SQLTableElement tableElement : ((SQLCreateTableStatement)statement).getTableElementList()) {
    SQLName sqlName=null;
    if (tableElement instanceof SQLColumnDefinition) {
      sqlName=((SQLColumnDefinition)tableElement).getName();
    }
    if (sqlName != null) {
      String simpleName=sqlName.getSimpleName();
      simpleName=StringUtil.removeBackquote(simpleName);
      if (tableElement instanceof SQLColumnDefinition && "_slot".equalsIgnoreCase(simpleName)) {
        return true;
      }
    }
  }
  return false;
}
```

## CM FN M149086 (MyCATApache_Mycat-Server); votes 2/2; in run: False; score 0.459

`/codesplit_java_method/MyCATApache_Mycat-Server/MyCATApache_Mycat-Server/io.mycat.route.util/RouterUtil/getRandomDataNode.code`

```java
@Deprecated private static String getRandomDataNode(TableConfig tc){
  String randomDn=tc.getRandomDataNode();
  MycatConfig mycatConfig=MycatServer.getInstance().getConfig();
  if (mycatConfig != null) {
    PhysicalDBNode physicalDBNode=mycatConfig.getDataNodes().get(randomDn);
    if (physicalDBNode != null) {
      if (physicalDBNode.getDbPool().getSource().isAlive()) {
        for (        PhysicalDBPool pool : MycatServer.getInstance().getConfig().getDataHosts().values()) {
          if (pool.getSource().getHostConfig().containDataNode(randomDn)) {
            continue;
          }
          if (pool.getSource().isAlive()) {
            return pool.getSource().getHostConfig().getRandomDataNode();
          }
        }
      }
    }
  }
  return randomDn;
}
```

## CM FN M152156 (igniterealtime_Smack); votes 2/2; in run: False; score 0.393

`/codesplit_java_method/igniterealtime_Smack/igniterealtime_Smack/org.jivesoftware.smack.util/EqualsUtil/equals.code`

```java
public static <T>boolean equals(T thisObject,Object other,EqualsComperator<T> equalsComperator){
  if (other == null) {
    return false;
  }
  if (thisObject == other) {
    return true;
  }
  @SuppressWarnings("unchecked") Class<T> thisObjectClass=(Class<T>)thisObject.getClass();
  if (thisObjectClass != other.getClass()) {
    return false;
  }
  int thisHashCode=thisObject.hashCode();
  int otherHashCode=other.hashCode();
  if (thisHashCode != otherHashCode) {
    return false;
  }
  EqualsUtil.Builder equalsBuilder=new EqualsUtil.Builder();
  equalsComperator.compare(equalsBuilder,thisObjectClass.cast(other));
  return equalsBuilder.isEquals;
}
```

## CM FN M158584 (igniterealtime_Smack); votes 2/2; in run: False; score 0.405

`/codesplit_java_method/igniterealtime_Smack/igniterealtime_Smack/org.igniterealtime.smack.inttest/SmackIntegrationTestFramework/invokeLowLevel.code`

```java
private List<ConcreteTest> invokeLowLevel(LowLevelTestMethod lowLevelTestMethod,AbstractSmackLowLevelIntegrationTest test){
  Collection<? extends XmppConnectionDescriptor<?,?,?>> connectionDescriptors;
  if (lowLevelTestMethod.smackIntegrationTestAnnotation.onlyDefaultConnectionType()) {
    XmppConnectionDescriptor<?,?,?> defaultConnectionDescriptor=connectionManager.getDefaultConnectionDescriptor();
    connectionDescriptors=Collections.singleton(defaultConnectionDescriptor);
  }
 else {
    connectionDescriptors=connectionManager.getConnectionDescriptors();
  }
  List<ConcreteTest> resultingConcreteTests=new ArrayList<>(connectionDescriptors.size());
  for (  XmppConnectionDescriptor<?,?,?> connectionDescriptor : connectionDescriptors) {
    String connectionNick=connectionDescriptor.getNickname();
    if (config.enabledConnections != null && !config.enabledConnections.contains(connectionNick)) {
      DisabledTest disabledTest=new DisabledTest(lowLevelTestMethod.testMethod,"Not creating test for " + lowLevelTestMethod + " with connection '"+ connectionNick+ "', as this connection type is not enabled");
      testRunResult.disabledTests.add(disabledTest);
      continue;
    }
    if (config.disabledConnections != null && config.disabledConnections.contains(connectionNick)) {
      DisabledTest disabledTest=new DisabledTest(lowLevelTestMethod.testMethod,"Not creating test for " + lowLevelTestMethod + " with connection '"+ connectionNick+ ", as this connection type is disabled");
      testRunResult.disabledTests.add(disabledTest);
      continue;
    }
    ConcreteTest.Executor executor=() -> lowLevelTestMethod.invoke(test,connectionDescriptor);
    ConcreteTest concreteTest=new ConcreteTest(TestType.LowLevel,lowLevelTestMethod.testMethod,executor,connectionDescriptor.getNickname());
    resultingConcreteTests.add(concreteTest);
  }
  return resultingConcreteTests;
}
```

## CM FN M163025 (lettuce-io_lettuce-core); votes 2/2; in run: False; score 0.458

`/codesplit_java_method/lettuce-io_lettuce-core/lettuce-io_lettuce-core/io.lettuce.core/RedisChannelHandler/dispatch.code`

```java
protected <T>RedisCommand<K,V,T> dispatch(RedisCommand<K,V,T> cmd){
  if (debugEnabled) {
    logger.debug("dispatching command {}",cmd);
  }
  if (tracingEnabled) {
    RedisCommand<K,V,T> commandToSend=cmd;
    TraceContextProvider provider=CommandWrapper.unwrap(cmd,TraceContextProvider.class);
    if (provider == null) {
      commandToSend=new TracedCommand<>(cmd,clientResources.tracing().initialTraceContextProvider().getTraceContext());
    }
    return channelWriter.write(commandToSend);
  }
  return channelWriter.write(cmd);
}
protected Collection<RedisCommand<K,V,?>> dispatch(Collection<? extends RedisCommand<K,V,?>> commands){
  if (debugEnabled) {
    logger.debug("dispatching commands {}",commands);
  }
  if (tracingEnabled) {
    Collection<RedisCommand<K,V,?>> withTracer=new ArrayList<>(commands.size());
    for (    RedisCommand<K,V,?> command : commands) {
      RedisCommand<K,V,?> commandToUse=command;
      TraceContextProvider provider=CommandWrapper.unwrap(command,TraceContextProvider.class);
      if (provider == null) {
        commandToUse=new TracedCommand<>(command,clientResources.tracing().initialTraceContextProvider().getTraceContext());
      }
      withTracer.add(commandToUse);
    }
    return channelWriter.write(withTracer);
  }
  return channelWriter.write(commands);
}
```

## CM FN M169457 (lettuce-io_lettuce-core); votes 2/2; in run: False; score 0.364

`/codesplit_java_method/lettuce-io_lettuce-core/lettuce-io_lettuce-core/io.lettuce.core.dynamic/DeclaredCommandMethod/equals.code`

```java
@Override public boolean equals(Object o){
  if (this == o)   return true;
  if (!(o instanceof DeclaredCommandMethod))   return false;
  DeclaredCommandMethod that=(DeclaredCommandMethod)o;
  if (method != null ? !method.equals(that.method) : that.method != null)   return false;
  if (returnType != null ? !returnType.equals(that.returnType) : that.returnType != null)   return false;
  return arguments != null ? arguments.equals(that.arguments) : that.arguments == null;
}
```

## CM FN M170922 (lettuce-io_lettuce-core); votes 2/2; in run: False; score 0.384

`/codesplit_java_method/lettuce-io_lettuce-core/lettuce-io_lettuce-core/io.lettuce.core.models.role/RoleParser/getMonitoredUpstreams.code`

```java
private static List<String> getMonitoredUpstreams(Iterator<?> iterator){
  List<String> monitoredUpstreams=new ArrayList<>();
  if (!iterator.hasNext()) {
    return monitoredUpstreams;
  }
  Object upstreams=iterator.next();
  if (!(upstreams instanceof Collection)) {
    return monitoredUpstreams;
  }
  for (  Object upstream : (Collection)upstreams) {
    if (upstream instanceof String) {
      monitoredUpstreams.add((String)upstream);
    }
  }
  return monitoredUpstreams;
}
```

## CM FN M171191 (lettuce-io_lettuce-core); votes 2/2; in run: False; score 0.392

`/codesplit_java_method/lettuce-io_lettuce-core/lettuce-io_lettuce-core/io.lettuce.core.output/StreamReadOutput/complete.code`

```java
@Override public void complete(int depth){
  if (depth == 3 && bodyReceived) {
    subscriber.onNext(output,new StreamMessage<>(stream,id,body == null ? Collections.emptyMap() : body));
    bodyReceived=false;
    key=null;
    body=null;
    id=null;
  }
  if (depth == 2 && skipStreamKeyReset) {
    skipStreamKeyReset=false;
  }
  if (depth == 1) {
    if (skipStreamKeyReset) {
      skipStreamKeyReset=false;
    }
 else {
      stream=null;
    }
  }
}
```

## CM FN M174536 (kevin-wayne_algs4); votes 2/2; in run: False; score 0.450

`/codesplit_java_method/kevin-wayne_algs4/kevin-wayne_algs4/edu.princeton.cs.algs4/BST/floor.code`

```java
/** 
 * Returns the largest key in the symbol table less than or equal to  {@code key}.
 * @param key the key
 * @return the largest key in the symbol table less than or equal to {@code key}
 * @throws NoSuchElementException if there is no such key
 * @throws IllegalArgumentException if {@code key} is {@code null}
 */
public Key floor(Key key){
  if (key == null)   throw new IllegalArgumentException("argument to floor() is null");
  if (isEmpty())   throw new NoSuchElementException("calls floor() with empty symbol table");
  Node x=floor(root,key);
  if (x == null)   throw new NoSuchElementException("argument to floor() is too small");
 else   return x.key;
}
private Node floor(Node x,Key key){
  if (x == null)   return null;
  int cmp=key.compareTo(x.key);
  if (cmp == 0)   return x;
  if (cmp < 0)   return floor(x.left,key);
  Node t=floor(x.right,key);
  if (t != null)   return t;
 else   return x;
}
```

## CM FN M174540 (kevin-wayne_algs4); votes 2/2; in run: False; score 0.466

`/codesplit_java_method/kevin-wayne_algs4/kevin-wayne_algs4/edu.princeton.cs.algs4/BST/ceiling.code`

```java
/** 
 * Returns the smallest key in the symbol table greater than or equal to  {@code key}.
 * @param key the key
 * @return the smallest key in the symbol table greater than or equal to {@code key}
 * @throws NoSuchElementException if there is no such key
 * @throws IllegalArgumentException if {@code key} is {@code null}
 */
public Key ceiling(Key key){
  if (key == null)   throw new IllegalArgumentException("argument to ceiling() is null");
  if (isEmpty())   throw new NoSuchElementException("calls ceiling() with empty symbol table");
  Node x=ceiling(root,key);
  if (x == null)   throw new NoSuchElementException("argument to ceiling() is too large");
 else   return x.key;
}
private Node ceiling(Node x,Key key){
  if (x == null)   return null;
  int cmp=key.compareTo(x.key);
  if (cmp == 0)   return x;
  if (cmp < 0) {
    Node t=ceiling(x.left,key);
    if (t != null)     return t;
 else     return x;
  }
  return ceiling(x.right,key);
}
```

## CM FN M180759 (MovingBlocks_Terasology); votes 2/2; in run: False; score 0.494

`/codesplit_java_method/MovingBlocks_Terasology/MovingBlocks_Terasology/org.terasology.engine.logic.players/ThirdPersonRemoteClientSystem/relatesToLocalPlayer.code`

```java
/** 
 * Checks a given entity in a variety of ways to see if it is immediately related to a local player. TODO: Is a bit of a shotgun blast approach to throwing out undesired player/client/character entities. Needs a more surgical approach.
 * @param entity the entity to check (probably a player, client, or character entity)
 * @return true if any such check passes, otherwise false
 */
private boolean relatesToLocalPlayer(EntityRef entity){
  if (entity == null || entity.equals(EntityRef.NULL)) {
    return false;
  }
  if (entity.equals(localPlayer.getClientEntity())) {
    return true;
  }
  if (entity.equals(localPlayer.getCharacterEntity())) {
    return true;
  }
  if (entity.equals(localPlayer.getClientInfoEntity())) {
    return true;
  }
  EntityRef networkSystemProvidedClientEntity=localPlayerSystem.getClientEntityViaNetworkSystem();
  if (entity.equals(networkSystemProvidedClientEntity)) {
    logger.debug("checkForLocalPlayer found its entity to match the network system provided local client " + "entity! {}",entity);
  }
  if (entity.hasComponent(CharacterComponent.class)) {
    EntityRef controller=entity.getComponent(CharacterComponent.class).controller;
    if (controller != null) {
      if (controller.equals(localPlayer.getClientEntity())) {
        return true;
      }
      if (controller.equals(networkSystemProvidedClientEntity)) {
        return true;
      }
    }
  }
  return false;
}
```

## CM FN M186883 (MovingBlocks_Terasology); votes 2/2; in run: False; score 0.412

`/codesplit_java_method/MovingBlocks_Terasology/MovingBlocks_Terasology/org.terasology.engine.world.block.entity/BlockEntitySystem/commonDefaultDropsHandling.code`

```java
public void commonDefaultDropsHandling(CreateBlockDropsEvent event,EntityRef entity,Vector3ic location,Block block){
  BlockDamageModifierComponent blockDamageModifierComponent=event.getDamageType().getComponent(BlockDamageModifierComponent.class);
  float chanceOfBlockDrop=1;
  if (blockDamageModifierComponent != null) {
    chanceOfBlockDrop=1 - blockDamageModifierComponent.blockAnnihilationChance;
  }
  if (random.nextFloat() < chanceOfBlockDrop) {
    EntityRef item=blockItemFactory.newInstance(block.getBlockFamily(),entity);
    entity.send(new OnBlockToItem(item));
    if (shouldDropToWorld(event,block,blockDamageModifierComponent,item)) {
      float impulsePower=0;
      if (blockDamageModifierComponent != null) {
        impulsePower=blockDamageModifierComponent.impulsePower;
      }
      processDropping(item,location,impulsePower);
    }
  }
}
```

## LPL FP M144613 (MyCATApache_Mycat-Server); votes 0/2; in run: True; score 0.541

`/codesplit_java_method/MyCATApache_Mycat-Server/MyCATApache_Mycat-Server/io.mycat.backend.mysql.nio.handler/UnLockTablesHandler/fieldEofResponse.code`

```java
@Override public void fieldEofResponse(byte[] header,List<byte[]> fields,byte[] eof,BackendConnection conn){
  LOGGER.error(new StringBuilder().append("unexpected packet for ").append(conn).append(" bound by ").append(session.getSource()).append(": field's eof").toString());
}
```

## LPL FP M148591 (MyCATApache_Mycat-Server); votes 0/2; in run: True; score 0.669

`/codesplit_java_method/MyCATApache_Mycat-Server/MyCATApache_Mycat-Server/io.mycat.route.parser.druid/DruidParser/visitorParse.code`

```java
/** 
 * 子类可覆盖（如果该方法解析得不到表名、字段等信息的，就覆盖该方法，覆盖成空方法，然后通过statementPparse去解析） 通过visitor解析：有些类型的Statement通过visitor解析得不到表名、
 * @param stmt
 */
public void visitorParse(SchemaConfig schema,RouteResultset rrs,SQLStatement stmt,MycatSchemaStatVisitor visitor) throws SQLNonTransientException ;
```

## LPL FP M156890 (igniterealtime_Smack); votes 0/2; in run: True; score 0.579

`/codesplit_java_method/igniterealtime_Smack/igniterealtime_Smack/org.jivesoftware.smackx.jingle/JingleUtil/createSessionTerminateContentCancel.code`

```java
public Jingle createSessionTerminateContentCancel(FullJid recipient,String sessionId,JingleContent.Creator contentCreator,String contentName){
  Jingle.Builder jb=Jingle.builder(connection);
  jb.setAction(JingleAction.session_terminate).setSessionId(sessionId);
  JingleContent.Builder cb=JingleContent.getBuilder();
  cb.setCreator(contentCreator).setName(contentName);
  Jingle jingle=jb.addJingleContent(cb.build()).build();
  jingle.setFrom(connection.getUser());
  jingle.setTo(recipient);
  return jingle;
}
```

## LPL FP M159640 (igniterealtime_Smack); votes 0/2; in run: True; score 0.726

`/codesplit_java_method/igniterealtime_Smack/igniterealtime_Smack/org.jivesoftware.smackx.jingleold.mediaimpl.jspeex/AudioMediaSession/AudioMediaSession.code`

```java
/** 
 * Creates a org.jivesoftware.jingleaudio.jspeex.AudioMediaSession with defined payload type, remote and local candidates.
 * @param payloadType Payload of the jmf
 * @param remote      the remote information. The candidate that the jmf will be sent to.
 * @param local       the local information. The candidate that will receive the jmf
 * @param locator     media locator
 * @param jingleSession the jingle session.
 */
public AudioMediaSession(final PayloadType payloadType,final TransportCandidate remote,final TransportCandidate local,String locator,JingleSession jingleSession){
  super(payloadType,remote,local,locator == null ? "dsound://" : locator,jingleSession);
  initialize();
}
```

## LPL FP M160947 (igniterealtime_Smack); votes 0/2; in run: False; score 0.637

`/codesplit_java_method/igniterealtime_Smack/igniterealtime_Smack/org.jivesoftware.smackx.ox.listener/SignElementReceivedListener/signElementReceived.code`

```java
/** 
 * A  {@link SignElement} has been received and successfully been verified.This listener is intended to be used by implementors of different OX usage profiles.
 * @param contact sender of the message
 * @param originalMessage original message containing the {@link SignElement}
 * @param signElement the {@link SignElement} itself
 * @param metadata metadata about the signing
 */
void signElementReceived(OpenPgpContact contact,Message originalMessage,SignElement signElement,OpenPgpMetadata metadata);
```

## LPL FP M162511 (lettuce-io_lettuce-core); votes 0/2; in run: True; score 0.577

`/codesplit_java_method/lettuce-io_lettuce-core/lettuce-io_lettuce-core/io.lettuce.core/AbstractRedisReactiveCommands/zrangestorebylex.code`

```java
@Override public Mono<Long> zrangestorebylex(K dstKey,K srcKey,Range<? extends V> range,Limit limit){
  return createMono(() -> commandBuilder.zrangestorebylex(dstKey,srcKey,range,limit,false));
}
```

## LPL FP M165323 (lettuce-io_lettuce-core); votes 0/2; in run: True; score 0.654

`/codesplit_java_method/lettuce-io_lettuce-core/lettuce-io_lettuce-core/io.lettuce.core.api/RedisScriptingCommands/evalReadOnly.code`

```java
/** 
 * This is a read-only variant of the EVAL command that cannot execute commands that modify data.
 * @param script Lua 5.1 script.
 * @param type the type.
 * @param keys the keys.
 * @param values the values.
 * @param < T > expected return type.
 * @return script result.
 * @since 6.2
 */
<T>T evalReadOnly(byte[] script,ScriptOutputType type,K[] keys,V... values);
```

## LPL FP M168702 (lettuce-io_lettuce-core); votes 0/2; in run: True; score 0.552

`/codesplit_java_method/lettuce-io_lettuce-core/lettuce-io_lettuce-core/io.lettuce.core.cluster.api.sync/NodeSelectionSortedSetCommands/zrevrange.code`

```java
/** 
 * Return a range of members in a sorted set, by index, with scores ordered from high to low.
 * @param key the key.
 * @param start the start.
 * @param stop the stop.
 * @return List&lt;V&gt; array-reply list of elements in the specified range.
 */
Executions<List<V>> zrevrange(K key,long start,long stop);
/** 
 * Stream over a range of members in a sorted set, by index, with scores ordered from high to low.
 * @param channel streaming channel that receives a call for every scored value.
 * @param key the key.
 * @param start the start.
 * @param stop the stop.
 * @return Long count of elements in the specified range.
 */
Executions<Long> zrevrange(ValueStreamingChannel<V> channel,K key,long start,long stop);
```

## LPL FP M174149 (lettuce-io_lettuce-core); votes 0/2; in run: True; score 0.546

`/codesplit_java_method/lettuce-io_lettuce-core/lettuce-io_lettuce-core/io.lettuce.test.resource/TestEventLoopGroupProvider/release.code`

```java
@Override public Promise<Boolean> release(EventExecutorGroup eventLoopGroup,long quietPeriod,long timeout,TimeUnit unit){
  DefaultPromise<Boolean> result=new DefaultPromise<>(ImmediateEventExecutor.INSTANCE);
  result.setSuccess(true);
  return result;
}
```

## LPL FP M179958 (MovingBlocks_Terasology); votes 0/2; in run: True; score 0.672

`/codesplit_java_method/MovingBlocks_Terasology/MovingBlocks_Terasology/org.terasology.engine.logic.characters/VisualCharacterSystemTest/simulateProperLinkingOfLocalPlayerAndCharacterEntities.code`

```java
private void simulateProperLinkingOfLocalPlayerAndCharacterEntities(EntityRef clientEntity,EntityRef otherClientEntity,EntityRef ownCharacterEntity,EntityRef otherCharacterEntity){
  clientEntityReturnedByLocalPlayer=clientEntity;
  Mockito.when(ownCharacterEntity.getOwner()).thenReturn(clientEntity);
  Mockito.when(otherCharacterEntity.getOwner()).thenReturn(otherClientEntity);
  Mockito.when(entityManager.getEntitiesWith(VisualCharacterComponent.class)).thenReturn(Arrays.asList(otherCharacterEntity,ownCharacterEntity));
}
```

## LPL FP M180422 (MovingBlocks_Terasology); votes 0/2; in run: True; score 0.537

`/codesplit_java_method/MovingBlocks_Terasology/MovingBlocks_Terasology/org.terasology.engine.logic.debug/MovementDebugCommands/teleportCommand.code`

```java
@Command(value="teleport",shortDescription="Teleports you to a location",runOnServer=true,requiredPermission=PermissionManager.CHEAT_PERMISSION) public String teleportCommand(@Sender EntityRef sender,@CommandParam("x") float x,@CommandParam("y") float y,@CommandParam("z") float z){
  ClientComponent clientComp=sender.getComponent(ClientComponent.class);
  clientComp.character.send(new CharacterTeleportEvent(new Vector3f(x,y,z)));
  return "Teleporting  to " + x + " "+ y+ " "+ z;
}
```

## LPL FP M180754 (MovingBlocks_Terasology); votes 0/2; in run: True; score 0.717

`/codesplit_java_method/MovingBlocks_Terasology/MovingBlocks_Terasology/org.terasology.engine.logic.players/ThirdPersonRemoteClientSystem/onHeldItemActivated.code`

```java
@ReceiveEvent public void onHeldItemActivated(OnActivatedComponent event,EntityRef player,CharacterHeldItemComponent heldItemComponent,CharacterComponent characterComponents){
  if (relatesToLocalPlayer(player)) {
    logger.debug("onHeldItemActivated found its given player to relate to the local player, ignoring: {}",player);
    return;
  }
  logger.debug("onHeldItemActivated says the given player is not the local player's character entity: {}",player);
  EntityRef newItem=heldItemComponent.selectedItem;
  linkHeldItemLocationForRemotePlayer(newItem,player);
}
```

## LPL FP M185578 (MovingBlocks_Terasology); votes 0/2; in run: True; score 0.658

`/codesplit_java_method/MovingBlocks_Terasology/MovingBlocks_Terasology/org.terasology.engine.rendering.opengl/OpenGLMesh/OpenGLMesh.code`

```java
public OpenGLMesh(ResourceUrn urn,AssetType<?,MeshData> assetType,MeshData data,DisposalAction disposalAction,LwjglGraphicsProcessing graphicsProcessing){
  super(urn,assetType,disposalAction);
  this.disposalAction=disposalAction;
  graphicsProcessing.asynchToDisplayThread(() -> {
    reload(data);
  }
);
}
```

## LPL FP M186796 (MovingBlocks_Terasology); votes 0/2; in run: True; score 0.602

`/codesplit_java_method/MovingBlocks_Terasology/MovingBlocks_Terasology/org.terasology.engine.world.block/BlockUriParseException/BlockUriParseException.code`

```java
public BlockUriParseException(){
}
public BlockUriParseException(String message){
  super(message);
}
public BlockUriParseException(String message,Throwable cause){
  super(message,cause);
}
public BlockUriParseException(Throwable cause){
  super(cause);
}
public BlockUriParseException(String message,Throwable cause,boolean enableSuppression,boolean writableStackTrace){
  super(message,cause,enableSuppression,writableStackTrace);
}
```

## LPL FP M5542 (Blankj_AndroidUtilCode); votes 0/2; in run: True; score 0.743

`/codesplit_java_method/Blankj_AndroidUtilCode/Blankj_AndroidUtilCode/com.blankj.bus/BusUtils/registerBus.code`

```java
private void registerBus(String tag,String className,String funName,String paramType,String paramName,boolean sticky,String threadMode){
  registerBus(tag,className,funName,paramType,paramName,sticky,threadMode,0);
}
private void registerBus(String tag,String className,String funName,String paramType,String paramName,boolean sticky,String threadMode,int priority){
  List<BusInfo> busInfoList=mTag_BusInfoListMap.get(tag);
  if (busInfoList == null) {
    busInfoList=new ArrayList<>();
    mTag_BusInfoListMap.put(tag,busInfoList);
  }
  busInfoList.add(new BusInfo(className,funName,paramType,paramName,sticky,threadMode,priority));
}
```

## LPL FN M1368 (Blankj_AndroidUtilCode); votes 2/2; in run: True; score 0.354

`/codesplit_java_method/Blankj_AndroidUtilCode/Blankj_AndroidUtilCode/com.blankj.utilcode.util/DiskCacheManager/DiskCacheManager.code`

```java
private DiskCacheManager(final File cacheDir,final long sizeLimit,final int countLimit){
  this.cacheDir=cacheDir;
  this.sizeLimit=sizeLimit;
  this.countLimit=countLimit;
  cacheSize=new AtomicLong();
  cacheCount=new AtomicInteger();
  mThread=new Thread(new Runnable(){
    @Override public void run(){
      int size=0;
      int count=0;
      final File[] cachedFiles=cacheDir.listFiles(new FilenameFilter(){
        @Override public boolean accept(        File dir,        String name){
          return name.startsWith(CACHE_PREFIX);
        }
      }
);
      if (cachedFiles != null) {
        for (        File cachedFile : cachedFiles) {
          size+=cachedFile.length();
          count+=1;
          lastUsageDates.put(cachedFile,cachedFile.lastModified());
        }
        cacheSize.getAndAdd(size);
        cacheCount.getAndAdd(count);
      }
    }
  }
);
  mThread.start();
}
```

## LPL FN M143069 (MyCATApache_Mycat-Server); votes 2/2; in run: True; score 0.487

`/codesplit_java_method/MyCATApache_Mycat-Server/MyCATApache_Mycat-Server/io.mycat.backend/ConnectionMeta/ConnectionMeta.code`

```java
public ConnectionMeta(String schema,String charset,int txIsolation,boolean autocommit){
  super();
  this.schema=schema;
  this.charset=charset;
  this.txIsolation=txIsolation;
  this.autocommit=autocommit;
}
```

## LPL FN M143814 (MyCATApache_Mycat-Server); votes 2/2; in run: True; score 0.487

`/codesplit_java_method/MyCATApache_Mycat-Server/MyCATApache_Mycat-Server/io.mycat.backend.jdbc.sequoiadb/DriverPropertyInfoHelper/addPropInfo.code`

```java
private void addPropInfo(final ArrayList<DriverPropertyInfo> propInfos,final String propName,final String defaultVal,final String description,final String[] choices){
  DriverPropertyInfo newProp=new DriverPropertyInfo(propName,defaultVal);
  newProp.description=description;
  if (choices != null) {
    newProp.choices=choices;
  }
  propInfos.add(newProp);
}
```

## LPL FN M146796 (MyCATApache_Mycat-Server); votes 2/2; in run: True; score 0.435

`/codesplit_java_method/MyCATApache_Mycat-Server/MyCATApache_Mycat-Server/io.mycat.memory.unsafe.ringbuffer.common.event/EventTranslatorTwoArg/translateTo.code`

```java
void translateTo(final T event,long sequence,final A arg0,final B arg1);
```

## LPL FN M148927 (MyCATApache_Mycat-Server); votes 2/2; in run: True; score 0.106

`/codesplit_java_method/MyCATApache_Mycat-Server/MyCATApache_Mycat-Server/io.mycat.route.parser.util/PageSQLUtil/convertLimitToNativePageSql.code`

```java
public static String convertLimitToNativePageSql(String dbType,String sql,int offset,int count){
  if (JdbcConstants.ORACLE.name().equalsIgnoreCase(dbType)) {
    OracleStatementParser oracleParser=new OracleStatementParser(sql);
    SQLSelectStatement oracleStmt=(SQLSelectStatement)oracleParser.parseStatement();
    return PagerUtils.limit(oracleStmt.getSelect(),JdbcConstants.ORACLE,offset,count);
  }
 else   if (JdbcConstants.SQL_SERVER.name().equalsIgnoreCase(dbType)) {
    SQLServerStatementParser oracleParser=new SQLServerStatementParser(sql);
    SQLSelectStatement sqlserverStmt=(SQLSelectStatement)oracleParser.parseStatement();
    SQLSelect select=sqlserverStmt.getSelect();
    SQLOrderBy orderBy=select.getOrderBy();
    if (orderBy == null) {
      SQLSelectQuery sqlSelectQuery=select.getQuery();
      if (sqlSelectQuery instanceof SQLServerSelectQueryBlock) {
        SQLServerSelectQueryBlock sqlServerSelectQueryBlock=(SQLServerSelectQueryBlock)sqlSelectQuery;
        SQLTableSource from=sqlServerSelectQueryBlock.getFrom();
        if ("limit".equalsIgnoreCase(from.getAlias())) {
          from.setAlias(null);
        }
      }
      SQLOrderBy newOrderBy=new SQLOrderBy(new SQLIdentifierExpr("(select 0)"));
      select.setOrderBy(newOrderBy);
    }
    return PagerUtils.limit(select,JdbcConstants.SQL_SERVER,offset,count);
  }
 else   if (JdbcConstants.DB2.name().equalsIgnoreCase(dbType)) {
    DB2StatementParser db2Parser=new DB2StatementParser(sql);
    SQLSelectStatement db2Stmt=(SQLSelectStatement)db2Parser.parseStatement();
    return limitDB2(db2Stmt.getSelect(),JdbcConstants.DB2.name(),offset,count);
  }
 else   if (JdbcConstants.POSTGRESQL.name().equalsIgnoreCase(dbType)) {
    PGSQLStatementParser pgParser=new PGSQLStatementParser(sql);
    SQLSelectStatement pgStmt=(SQLSelectStatement)pgParser.parseStatement();
    SQLSelect select=pgStmt.getSelect();
    SQLSelectQuery query=select.getQuery();
    if (query instanceof PGSelectQueryBlock) {
      PGSelectQueryBlock pgSelectQueryBlock=(PGSelectQueryBlock)query;
      pgSelectQueryBlock.setOffset(null);
      pgSelectQueryBlock.setLimit(null);
    }
    return PagerUtils.limit(select,JdbcConstants.POSTGRESQL,offset,count);
  }
 else   if (JdbcConstants.MYSQL.name().equalsIgnoreCase(dbType)) {
    MySqlStatementParser pgParser=new MySqlStatementParser(sql);
    SQLSelectStatement pgStmt=(SQLSelectStatement)pgParser.parseStatement();
    SQLSelect select=pgStmt.getSelect();
    SQLSelectQuery query=select.getQuery();
    if (query instanceof MySqlSelectQueryBlock) {
      MySqlSelectQueryBlock pgSelectQueryBlock=(MySqlSelectQueryBlock)query;
      pgSelectQueryBlock.setLimit(null);
    }
    return PagerUtils.limit(select,JdbcConstants.MYSQL,offset,count);
  }
  return sql;
}
```

## LPL FN M151980 (igniterealtime_Smack); votes 2/2; in run: False; score 0.499

`/codesplit_java_method/igniterealtime_Smack/igniterealtime_Smack/org.jivesoftware.smack.packet/StreamOpen/StreamOpen.code`

```java
public StreamOpen(CharSequence to){
  this(to,null,null,null,StreamContentNamespace.client);
}
public StreamOpen(CharSequence to,CharSequence from,String id){
  this(to,from,id,"en",StreamContentNamespace.client);
}
public StreamOpen(CharSequence to,CharSequence from,String id,String lang){
  super(to,from,id,lang);
}
public StreamOpen(CharSequence to,CharSequence from,String id,String lang,StreamContentNamespace ns){
  super(to,from,id,lang,ns);
}
```

## LPL FN M158625 (igniterealtime_Smack); votes 2/2; in run: False; score 0.385

`/codesplit_java_method/igniterealtime_Smack/igniterealtime_Smack/org.igniterealtime.smack.inttest/XmppConnectionManager/constructConnection.code`

```java
AbstractXMPPConnection constructConnection() throws NoResponseException, XMPPErrorException, NotConnectedException, InterruptedException {
  return constructConnection(defaultConnectionDescriptor);
}
<C extends AbstractXMPPConnection>C constructConnection(XmppConnectionDescriptor<C,? extends ConnectionConfiguration,? extends ConnectionConfiguration.Builder<?,?>> connectionDescriptor) throws NoResponseException, XMPPErrorException, NotConnectedException, InterruptedException {
  return constructConnection(connectionDescriptor,null);
}
private <C extends AbstractXMPPConnection>C constructConnection(XmppConnectionDescriptor<C,? extends ConnectionConfiguration,? extends ConnectionConfiguration.Builder<?,?>> connectionDescriptor,Collection<ConnectionConfigurationBuilderApplier> customConnectionConfigurationAppliers) throws NoResponseException, XMPPErrorException, NotConnectedException, InterruptedException {
  String username="sinttest-" + testRunId + '-'+ (connections.size() + 1);
  String password=StringUtils.randomString(24);
  return constructConnection(username,password,connectionDescriptor,customConnectionConfigurationAppliers);
}
private <C extends AbstractXMPPConnection>C constructConnection(final String username,final String password,XmppConnectionDescriptor<C,? extends ConnectionConfiguration,? extends ConnectionConfiguration.Builder<?,?>> connectionDescriptor,Collection<ConnectionConfigurationBuilderApplier> customConnectionConfigurationAppliers) throws NoResponseException, XMPPErrorException, NotConnectedException, InterruptedException {
  try {
    registerAccount(username,password);
  }
 catch (  XmppStringprepException e) {
    throw new IllegalArgumentException(e);
  }
  ConnectionConfigurationBuilderApplier usernameAndPasswordApplier=configurationBuilder -> {
    configurationBuilder.setUsernameAndPassword(username,password);
  }
;
  if (customConnectionConfigurationAppliers == null) {
    customConnectionConfigurationAppliers=Collections.singleton(usernameAndPasswordApplier);
  }
 else {
    customConnectionConfigurationAppliers.add(usernameAndPasswordApplier);
  }
  C connection;
  try {
    connection=connectionDescriptor.construct(sinttestConfiguration,customConnectionConfigurationAppliers);
  }
 catch (  InstantiationException|IllegalAccessException|IllegalArgumentException|InvocationTargetException e) {
    throw new IllegalStateException(e);
  }
  connections.put(connection,connectionDescriptor);
  return connection;
}
```

## LPL FN M161967 (lettuce-io_lettuce-core); votes 2/2; in run: False; score 0.480

`/codesplit_java_method/lettuce-io_lettuce-core/lettuce-io_lettuce-core/io.lettuce.core/AbstractRedisAsyncCommands/zrevrangebyscoreWithScores.code`

```java
@Override public RedisFuture<List<ScoredValue<V>>> zrevrangebyscoreWithScores(K key,double max,double min){
  return dispatch(commandBuilder.zrevrangebyscoreWithScores(key,max,min));
}
@Override public RedisFuture<List<ScoredValue<V>>> zrevrangebyscoreWithScores(K key,String max,String min){
  return dispatch(commandBuilder.zrevrangebyscoreWithScores(key,max,min));
}
@Override public RedisFuture<List<ScoredValue<V>>> zrevrangebyscoreWithScores(K key,Range<? extends Number> range){
  return dispatch(commandBuilder.zrevrangebyscoreWithScores(key,range,Limit.unlimited()));
}
@Override public RedisFuture<List<ScoredValue<V>>> zrevrangebyscoreWithScores(K key,double max,double min,long offset,long count){
  return dispatch(commandBuilder.zrevrangebyscoreWithScores(key,max,min,offset,count));
}
@Override public RedisFuture<List<ScoredValue<V>>> zrevrangebyscoreWithScores(K key,String max,String min,long offset,long count){
  return dispatch(commandBuilder.zrevrangebyscoreWithScores(key,max,min,offset,count));
}
@Override public RedisFuture<List<ScoredValue<V>>> zrevrangebyscoreWithScores(K key,Range<? extends Number> range,Limit limit){
  return dispatch(commandBuilder.zrevrangebyscoreWithScores(key,range,limit));
}
@Override public RedisFuture<Long> zrevrangebyscoreWithScores(ScoredValueStreamingChannel<V> channel,K key,double max,double min){
  return dispatch(commandBuilder.zrevrangebyscoreWithScores(channel,key,max,min));
}
@Override public RedisFuture<Long> zrevrangebyscoreWithScores(ScoredValueStreamingChannel<V> channel,K key,String max,String min){
  return dispatch(commandBuilder.zrevrangebyscoreWithScores(channel,key,max,min));
}
@Override public RedisFuture<Long> zrevrangebyscoreWithScores(ScoredValueStreamingChannel<V> channel,K key,Range<? extends Number> range){
  return dispatch(commandBuilder.zrevrangebyscoreWithScores(channel,key,range,Limit.unlimited()));
}
@Override public RedisFuture<Long> zrevrangebyscoreWithScores(ScoredValueStreamingChannel<V> channel,K key,double max,double min,long offset,long count){
  return dispatch(commandBuilder.zrevrangebyscoreWithScores(channel,key,max,min,offset,count));
}
@Override public RedisFuture<Long> zrevrangebyscoreWithScores(ScoredValueStreamingChannel<V> channel,K key,String max,String min,long offset,long count){
  return dispatch(commandBuilder.zrevrangebyscoreWithScores(channel,key,max,min,offset,count));
}
@Override public RedisFuture<Long> zrevrangebyscoreWithScores(ScoredValueStreamingChannel<V> channel,K key,Range<? extends Number> range,Limit limit){
  return dispatch(commandBuilder.zrevrangebyscoreWithScores(channel,key,range,limit));
}
```

## LPL FN M163244 (lettuce-io_lettuce-core); votes 2/2; in run: False; score 0.499

`/codesplit_java_method/lettuce-io_lettuce-core/lettuce-io_lettuce-core/io.lettuce.core/RedisCommandBuilder/hello.code`

```java
Command<String,String,Map<String,Object>> hello(int protocolVersion,String user,char[] password,String name){
  CommandArgs<String,String> args=new CommandArgs<>(StringCodec.ASCII).add(protocolVersion);
  if (user != null && password != null) {
    args.add(AUTH).add(user).add(password);
  }
  if (name != null) {
    args.add(SETNAME).add(name);
  }
  return new Command<>(HELLO,new GenericMapOutput<>(StringCodec.ASCII),args);
}
```

## LPL FN M163568 (lettuce-io_lettuce-core); votes 2/2; in run: True; score 0.343

`/codesplit_java_method/lettuce-io_lettuce-core/lettuce-io_lettuce-core/io.lettuce.core/RedisCommandBuilder/zrevrangebyscoreWithScores.code`

```java
Command<K,V,List<ScoredValue<V>>> zrevrangebyscoreWithScores(K key,double max,double min){
  return zrevrangebyscoreWithScores(key,string(max),string(min));
}
Command<K,V,List<ScoredValue<V>>> zrevrangebyscoreWithScores(K key,String max,String min){
  notNullKey(key);
  notNullMinMax(min,max);
  CommandArgs<K,V> args=new CommandArgs<>(codec);
  args.addKey(key).add(max).add(min).add(WITHSCORES);
  return createCommand(ZREVRANGEBYSCORE,new ScoredValueListOutput<>(codec),args);
}
Command<K,V,List<ScoredValue<V>>> zrevrangebyscoreWithScores(K key,double max,double min,long offset,long count){
  return zrevrangebyscoreWithScores(key,string(max),string(min),offset,count);
}
Command<K,V,List<ScoredValue<V>>> zrevrangebyscoreWithScores(K key,String max,String min,long offset,long count){
  notNullKey(key);
  notNullMinMax(min,max);
  CommandArgs<K,V> args=new CommandArgs<>(codec);
  addLimit(args.addKey(key).add(max).add(min).add(WITHSCORES),Limit.create(offset,count));
  return createCommand(ZREVRANGEBYSCORE,new ScoredValueListOutput<>(codec),args);
}
Command<K,V,List<ScoredValue<V>>> zrevrangebyscoreWithScores(K key,Range<? extends Number> range,Limit limit){
  notNullKey(key);
  notNullRange(range);
  notNullLimit(limit);
  CommandArgs<K,V> args=new CommandArgs<>(codec);
  addLimit(args.addKey(key).add(max(range)).add(min(range)).add(WITHSCORES),limit);
  return createCommand(ZREVRANGEBYSCORE,new ScoredValueListOutput<>(codec),args);
}
Command<K,V,Long> zrevrangebyscoreWithScores(ScoredValueStreamingChannel<V> channel,K key,double max,double min){
  return zrevrangebyscoreWithScores(channel,key,string(max),string(min));
}
Command<K,V,Long> zrevrangebyscoreWithScores(ScoredValueStreamingChannel<V> channel,K key,String max,String min){
  notNullKey(key);
  notNullMinMax(min,max);
  notNull(channel);
  CommandArgs<K,V> args=new CommandArgs<>(codec);
  args.addKey(key).add(max).add(min).add(WITHSCORES);
  return createCommand(ZREVRANGEBYSCORE,new ScoredValueStreamingOutput<>(codec,channel),args);
}
Command<K,V,Long> zrevrangebyscoreWithScores(ScoredValueStreamingChannel<V> channel,K key,double max,double min,long offset,long count){
  notNullKey(key);
  LettuceAssert.notNull(min,"Min " + MUST_NOT_BE_NULL);
  LettuceAssert.notNull(max,"Max " + MUST_NOT_BE_NULL);
  notNull(channel);
  return zrevrangebyscoreWithScores(channel,key,string(max),string(min),offset,count);
}
Command<K,V,Long> zrevrangebyscoreWithScores(ScoredValueStreamingChannel<V> channel,K key,String max,String min,long offset,long count){
  notNullKey(key);
  notNullMinMax(min,max);
  notNull(channel);
  CommandArgs<K,V> args=new CommandArgs<>(codec);
  addLimit(args.addKey(key).add(max).add(min).add(WITHSCORES),Limit.create(offset,count));
  return createCommand(ZREVRANGEBYSCORE,new ScoredValueStreamingOutput<>(codec,channel),args);
}
Command<K,V,Long> zrevrangebyscoreWithScores(ScoredValueStreamingChannel<V> channel,K key,Range<? extends Number> range,Limit limit){
  notNullKey(key);
  notNullRange(range);
  notNullLimit(limit);
  notNull(channel);
  CommandArgs<K,V> args=new CommandArgs<>(codec);
  addLimit(args.addKey(key).add(max(range)).add(min(range)).add(WITHSCORES),limit);
  return createCommand(ZREVRANGEBYSCORE,new ScoredValueStreamingOutput<>(codec,channel),args);
}
```

## LPL FN M171632 (lettuce-io_lettuce-core); votes 2/2; in run: True; score 0.469

`/codesplit_java_method/lettuce-io_lettuce-core/lettuce-io_lettuce-core/io.lettuce.core.protocol/RedisStateMachine/handleBulkError.code`

```java
static State.Result handleBulkError(RedisStateMachine rsm,State state,ByteBuf buffer,CommandOutput<?,?,?> output,Consumer<Exception> errorHandler){
  int length;
  int end;
  if ((end=rsm.findLineEnd(buffer)) == NOT_FOUND) {
    return State.Result.BREAK_LOOP;
  }
  length=(int)rsm.readLong(buffer,buffer.readerIndex(),end);
  if (length == NOT_FOUND) {
    rsm.safeSetError(output,null,errorHandler);
  }
 else {
    state.type=BYTES;
    state.count=length + TERMINATOR_LENGTH;
    buffer.markReaderIndex();
    return State.Result.CONTINUE_LOOP;
  }
  return State.Result.NORMAL_END;
}
```

## LPL FN M174229 (kevin-wayne_algs4); votes 2/2; in run: True; score 0.460

`/codesplit_java_method/kevin-wayne_algs4/kevin-wayne_algs4/edu.princeton.cs.algs4/AmericanFlag/insertion.code`

```java
private static void insertion(String[] a,int lo,int hi,int d){
  for (int i=lo; i <= hi; i++)   for (int j=i; j > lo && less(a[j],a[j - 1],d); j--)   exch(a,j,j - 1);
}
private static void insertion(int[] a,int lo,int hi,int d){
  for (int i=lo; i <= hi; i++)   for (int j=i; j > lo && less(a[j],a[j - 1],d); j--)   exch(a,j,j - 1);
}
```

## LPL FN M174237 (kevin-wayne_algs4); votes 2/2; in run: True; score 0.460

`/codesplit_java_method/kevin-wayne_algs4/kevin-wayne_algs4/edu.princeton.cs.algs4/AmericanFlagX/insertion.code`

```java
private static void insertion(String[] a,int lo,int hi,int d){
  for (int i=lo; i <= hi; i++)   for (int j=i; j > lo && less(a[j],a[j - 1],d); j--)   exch(a,j,j - 1);
}
```

## LPL FN M187483 (MovingBlocks_Terasology); votes 2/2; in run: True; score 0.451

`/codesplit_java_method/MovingBlocks_Terasology/MovingBlocks_Terasology/org.terasology.engine.world.chunks.blockdata/TeraDenseArray16Bit/set.code`

```java
@Override public int set(int x,int y,int z,int value){
  int pos=pos(x,y,z);
  int old=data[pos];
  data[pos]=(short)value;
  return old;
}
@Override public boolean set(int x,int y,int z,int value,int expected){
  int pos=pos(x,y,z);
  int old=data[pos];
  if (old == expected) {
    data[pos]=(short)value;
    return true;
  }
  return false;
}
```

## LPL FN M52796 (shuzheng_zheng); votes 2/2; in run: False; score 0.376

`/codesplit_java_method/shuzheng_zheng/shuzheng_zheng/com.zheng.cms.web.controller/QaController/category.code`

```java
/** 
 * 类目页
 * @param alias
 * @param page
 * @param request
 * @param model
 * @return
 */
@RequestMapping(value="/category/{alias}",method=RequestMethod.GET) public String category(@PathVariable("alias") String alias,@RequestParam(required=false,defaultValue="1",value="page") int page,HttpServletRequest request,Model model){
  CmsSystemExample cmsSystemExample=new CmsSystemExample();
  cmsSystemExample.createCriteria().andCodeEqualTo(CODE);
  CmsSystem system=cmsSystemService.selectFirstByExample(cmsSystemExample);
  model.addAttribute("system",system);
  CmsCategoryExample cmsCategoryExample=new CmsCategoryExample();
  cmsCategoryExample.createCriteria().andSystemIdEqualTo(system.getSystemId()).andAliasEqualTo(alias);
  CmsCategory category=cmsCategoryService.selectFirstByExample(cmsCategoryExample);
  model.addAttribute("category",category);
  int rows=10;
  List<CmsArticle> articles=cmsArticleService.selectCmsArticlesByCategoryId(category.getCategoryId(),(page - 1) * rows,rows);
  model.addAttribute("articles",articles);
  long total=cmsArticleService.countByCategoryId(category.getCategoryId());
  Paginator paginator=new Paginator(total,page,rows,request);
  model.addAttribute("paginator",paginator);
  return thymeleaf("/qa/category/index");
}
```

